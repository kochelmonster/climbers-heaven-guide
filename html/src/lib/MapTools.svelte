<script lang="coffee">
import { createEventDispatcher } from 'svelte'
import FaBullseye from 'svelte-icons/fa/FaBullseye.svelte'
import FaExpandArrowsAlt from 'svelte-icons/fa/FaExpandArrowsAlt.svelte'


dispatch = createEventDispatcher();

export gps = false

click_gps = () -> 
	gps = !gps
	dispatch('click-gps', gps)


click_bounds = () ->
	dispatch('click-bounds')
</script>

<style>
	.selected {
        color: rgb(var(--color-secondary-800));
	}
	
	button {
		width: 2rem;
		height: 2rem;
		border: 0;
		background-color: transparent;
        /*color: rgb(var(--color-primary-800));*/
	}

	#button-bounds {
		display: none;
	}

	:global(.zoomed) #button-bounds {
		display: block;
	}
</style>

<button type="button" on:click={click_bounds} id="button-bounds" class="mb-2" title="Zoom to bounds">
    <FaExpandArrowsAlt/>
</button>

<button type="button" on:click={click_gps} class:selected={gps} id="button-gps" title="Show your location">
    <FaBullseye/>
</button>

