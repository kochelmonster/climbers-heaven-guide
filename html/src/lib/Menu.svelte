<button class="icon inline-block sticky top-2 z-10 float-right mr-3" use:popup={popupMenu}>
    <FaBars/>
</button>


<div class="card shadow-xl py-1 z-50" data-popup="popupMenu">
<div data-grid>
booking{3}
hdivider
careas{4}
hdivider
home{5}
hdivider
sector
</div>
</div>

<hr data-field="hdivider"/>
<a data-field="booking" class="px-4 whitespace-nowrap" href="https://www.climbers-heaven.me" tabindex="1" target="_blank">{$t`Booking`}</a>
<a data-field="careas" class="px-4 whitespace-nowrap" href="#the-climbing-areas" tabindex="1">{$t`Climbing Areas`}</a>
<a data-field="home" class="px-4 whitespace-nowrap" href="#climbing-in-montenegro" tabindex="1">{$t`Home`}</a>
<a data-field="sector" class="px-4 whitespace-nowrap" href="javascript:void(0)" on:click={move_to_sector}  tabindex="1">{$t`Move to current Sector`}</a>

<style>
	.icon {
		width: 1.5em;
		height: 1.5em;
	}

	a {
		padding: 4pt 10pt;
	}
</style>


<script lang="coffee">
import { t } from 'svelte-i18n-lingui'
import FaBars from 'svelte-icons/fa/FaBars.svelte'
import { popup } from '@skeletonlabs/skeleton'


move_to_sector = () ->
	overview.find_nearest_sector()


popupMenu =
	event: 'click',
	target: 'popupMenu',
	placement: 'bottom'

back_button = null
big_menu = null
</script>