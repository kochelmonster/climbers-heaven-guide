<script lang="coffee">
import { createEventDispatcher } from 'svelte'
import { t } from 'svelte-i18n-lingui'
import FaBullseye from 'svelte-icons/fa/FaBullseye.svelte'
import FaCompressArrowsAlt from 'svelte-icons/fa/FaCompressArrowsAlt.svelte'
import FaCog from 'svelte-icons/fa/FaCog.svelte'
import FaExpandArrowsAlt from 'svelte-icons/fa/FaExpandArrowsAlt.svelte'
import FaVectorSquare from 'svelte-icons/fa/FaVectorSquare.svelte'


dispatch = createEventDispatcher();

export gps = false
export fullscreen = false

click_gps = () -> 
	gps = !gps
	dispatch('click-gps', gps)


click_bounds = () ->
	dispatch('click-bounds')


click_configure = () ->
	dispatch('click-configure')


click_fullscreen = () ->
	dispatch('click-fullscreen')
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
	<FaVectorSquare/>
</button>

<button type="button" on:click={click_fullscreen} class:selected={fullscreen} class="mb-2" id="button-fullscreen" title={$t`Toggle map full window`}>
	{#if fullscreen}
		<FaCompressArrowsAlt/>
	{:else}
		<FaExpandArrowsAlt/>
	{/if}
</button>

<button type="button" on:click={click_configure} class="mb-2" id="button-configure" title={$t`Configure map provider`}>
	<FaCog/>
</button>

<button type="button" on:click={click_gps} class:selected={gps} id="button-gps" title="Show your location">
    <FaBullseye/>
</button>

