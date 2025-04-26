<script>
	import { onMount } from 'svelte';
	import axios from 'axios';

	const API_ENDPOINT =
		process.env.NODE_ENV === 'development'
			? 'http://localhost:8000/query'
			: 'https://jobs-api.nester.co.il/query';

	const JOBS_ENDPOINT =
		process.env.NODE_ENV === 'development'
			? 'http://localhost:8000/jobs_entities'
			: 'https://jobs-api.nester.co.il/jobs_entities';

	// At least one entity must be extracted from user's prompt to trigger search:
	const REQUIRED_ENTITIES = ['job_title', 'skills'];

	let textInput;
	let entities = [];
	let jobs = [];

	let debounceHandler;

	async function sendNluRequest(text) {
		const headers = { 'Content-Type': 'application/json' };
		const data = { text };
		try {
			const response = await axios.post(API_ENDPOINT, data, { headers });
			return response.data.entities || [];
		} catch (error) {
			console.error(error);
			return [];
		}
	}

	async function getJobs(entities) {
		const headers = { 'Content-Type': 'application/json' };
		try {
			const response = await axios.post(JOBS_ENDPOINT, entities, { headers });
			return response.data || [];
		} catch (error) {
			console.error(error);
			return [];
		}
	}

	function debounce(func, delay) {
		clearTimeout(debounceHandler);
		debounceHandler = setTimeout(func, delay);
	}

	async function handleKeyPress() {
		const text = textInput.value.trim();
		debounce(async () => {
			entities = await sendNluRequest(text);
			const filteredEntities = entities.filter((entity) =>
				REQUIRED_ENTITIES.includes(entity.entity)
			);
			if (filteredEntities.length > 0) {
				jobs = await getJobs(entities);
			} else {
				// Clean table
				jobs = [];
			}
		}, 400);
	}

	onMount(() => {
		textInput.focus();
	});
</script>

<h1>Welcome to Jobs</h1>

<p class="question">Tell me about your skills and the job you're looking for</p>
<input type="text" class="input-field" bind:this={textInput} on:input={handleKeyPress} />

<div id="entityList">
	{#each entities as entity}
		<span class={`entity-item entity-${entity.entity.toLowerCase().replace('_', '-')}`}
			>{`${entity.entity}: ${entity.value}`}</span
		>
	{/each}
</div>

{#if jobs.length > 0}
	<table class="jobs-table">
		<thead>
			<tr>
				<th>ID</th>
				<th>Job Title</th>
				<th>Company Name</th>
				<th>Job Location</th>
				<th>Posted Date</th>
				<th>Contact</th>
				<th>Work Type</th>
				<!-- <th>Description</th> -->
			</tr>
		</thead>
		<tbody>
			{#each jobs as job}
				<tr>
					<td>{job.job_id}</td>
					<td>{job.job_title}</td>
					<td>{job.company_name}</td>
					<td>{job.job_location}</td>
					<td>{job.posted_date}</td>
					<td><a href={job.contact}>{job.contact}</a></td>
					<td>{job.workplace_type}</td>
					<!-- <td>{job.job_description}</td> -->
				</tr>
			{/each}
		</tbody>
	</table>
{/if}

<style>
	.input-field {
		width: 500px;
		height: 40px;
		font-size: 18px;
		margin: 0 auto;
		margin-bottom: 20px;
		display: block;
	}

	.question {
		text-align: center;
		font-size: 18px;
	}

	.entity-list {
		margin-top: 20px;
		display: flex;
		flex-wrap: wrap;
	}

	.entity-item {
		padding: 4px 8px;
		margin-right: 8px;
		margin-bottom: 8px;
		border-radius: 4px;
		font-size: 14px;
		font-weight: bold;
	}

	.entity-job-title {
		background-color: #ffcc80;
	}

	.entity-job-location {
		background-color: #b3e5fc;
	}

	.entity-workplace-type {
		background-color: #c5e1a5;
	}

	.entity-skills {
		background-color: #f8bbd0;
	}

	.jobs-table {
		margin-top: 20px;
		border-collapse: collapse;
		width: 100%;
	}

	.jobs-table th,
	.jobs-table td {
		padding: 8px;
		text-align: left;
		border-bottom: 1px solid #ddd;
	}

	.jobs-table th {
		background-color: #f2f2f2;
	}
</style>
