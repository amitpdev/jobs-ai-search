import logging
import os
from typing import Dict, Text, Any, List, Optional

from rasa.engine.graph import GraphComponent, ExecutionContext
from rasa.engine.recipes.default_recipe import DefaultV1Recipe
from rasa.engine.storage.resource import Resource
from rasa.engine.storage.storage import ModelStorage
from rasa.shared.nlu.training_data.message import Message
from rasa.shared.nlu.training_data.training_data import TrainingData
from rasa.nlu.extractors.extractor import EntityExtractorMixin
from rasa.shared.nlu.constants import ENTITIES
from rasa.shared.constants import DOCS_URL_TRAINING_DATA
from rasa.nlu.utils import write_json_to_file
from rasa.shared.utils.io import read_json_file, raise_warning
from difflib import get_close_matches, SequenceMatcher

logger = logging.getLogger(__name__)

CLOSEST_MATCH_MIN_SCORE=0.6
SIMILARITY_MIN_SCORE=0.6
DIET_MIN_SCORE=0.1

@DefaultV1Recipe.register(
    [DefaultV1Recipe.ComponentType.ENTITY_EXTRACTOR], is_trainable=True
)
class Speller(GraphComponent, EntityExtractorMixin):

    LOOKUP_TABLES_FILENAME = "lookup_tables.json"
    KEYWORD_ENTITIES = ['job_location', 'workplace_type']

    def __init__(
        self,
        config: Optional[Dict[Text, Any]],
        model_storage: ModelStorage,
        resource: Resource,
        lookup_tables: Optional[List[Dict[Text, Any]]] = None,
    ) -> None:
        self._config = config
        self._model_storage = model_storage
        self._resource = resource
        self.lookup_tables = lookup_tables if lookup_tables else []

    @classmethod
    def create(
        cls,
        config: Dict[Text, Any],
        model_storage: ModelStorage,
        resource: Resource,
        execution_context: ExecutionContext,
        lookup_tables: Optional[List[Dict[Text, Any]]] = None):
        """Creates component (see parent class for full docstring)."""
        return cls(config, model_storage, resource, lookup_tables)

    def train(self, training_data: TrainingData) -> Resource:
        self.lookup_tables = training_data.lookup_tables
        self._persist()
        return self._resource

    def process(self, messages: List[Message]) -> List[Message]:

        for message in messages:
            previous_entities = message.data.get(ENTITIES, [])
            logger.debug(f'Previous pipeline entities: {previous_entities}')
            updated_entities = []
            for entity in previous_entities:
                # Skip/Remove ANY entity with low enough confidence
                if entity['confidence_entity'] < DIET_MIN_SCORE:
                    logger.debug(f'Removing low confidence entity: {entity}')
                    continue

                updated_entities.append(entity)

                entity_name = entity.get('entity')
                entity_value = entity.get('value')

                # Only run Speller on keyword entities ( not semantic ones )
                if entity_name not in Speller.KEYWORD_ENTITIES:
                    continue

                # Locate a lookup table for this entity type
                for lookup_dict in self.lookup_tables:
                    if entity_name == lookup_dict.get('name'):
                        lookup = lookup_dict.get('elements')
                if lookup is None:
                    continue

                # lookup table found, similar search entity value against lookup table
                new_value, score = self._spell_checker(entity_value, lookup)
                if not (score >= SIMILARITY_MIN_SCORE and new_value != entity_value):
                    logger.debug(f"Keep original: '{entity_value}' (score was: {score})")
                    continue

                # modify entity object (already in updated_entities)
                logger.debug(f"Replacing: '{entity_value}' with '{new_value}'")
                entity['value'] = new_value
                entity['extractor'] = 'Speller'
                entity['confidence_entity'] = score

            message.set(ENTITIES, updated_entities, add_to_output=True)

        return messages

    def _persist(self) -> None:
        if self.lookup_tables:
            with self._model_storage.write_to(self._resource) as storage:
                lookup_tables_file = storage / Speller.LOOKUP_TABLES_FILENAME
                write_json_to_file(
                    lookup_tables_file, self.lookup_tables, separators=(",", ": ")
                )

    # Adapt to get path from model storage and resource
    @classmethod
    def load(
        cls,
        config: Dict[Text, Any],
        model_storage: ModelStorage,
        resource: Resource,
        execution_context: ExecutionContext,
        **kwargs: Any,
    ) -> GraphComponent:
        """Loads trained component (see parent class for full docstring)."""
        lookup_tables_json = None
        try:
            with model_storage.read_from(resource) as storage:
                lookup_tables_file = storage / Speller.LOOKUP_TABLES_FILENAME

                if os.path.isfile(lookup_tables_file):
                    lookup_tables_json = read_json_file(lookup_tables_file)
                else:
                    lookup_tables_json = None
                    raise_warning(
                        f"Failed to load lookup tables file from '{lookup_tables_file}'.",
                        docs=DOCS_URL_TRAINING_DATA + "#speller",
                    )
        except ValueError:
            logger.debug(
                f"Failed to load {cls.__class__.__name__} from model storage. Resource "
                f"'{resource.name}' doesn't exist."
            )
        return cls(config, model_storage, resource, lookup_tables_json)

    def _spell_checker(self, keyword, predefined_keywords) -> tuple[str, float]:
        """
        Try to match `keyword` and an item in predefined_keywords list, if a good enough
        match was found, return matched string from predefined_keywords and similarity score.
        If no match was found, return the original keyword.

        i.e
        "sftwar engineer" -> "Software Engineer", 0.77
        or return 0 if no match was found:
        "balblabla" -> "balblabla", 0.0
        """
        matches = get_close_matches(keyword, predefined_keywords, n=1, cutoff=CLOSEST_MATCH_MIN_SCORE)
        if matches:
            closest_match = matches[0]
            similarity_score = SequenceMatcher(None, keyword, closest_match).ratio()
            logger.debug(f"Best match: {closest_match}, score: {similarity_score}")
            return closest_match, similarity_score
        return keyword, 0
