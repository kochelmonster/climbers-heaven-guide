<div id="splash" class="fixed top-0 lef-0 flex flex-col justify-center items-center z-40">
    <img src="favicon.svg" alt="loading" />
    <div class="blink-me">Loading...</div>
</div>

<div data-grid class="box-border h-full w-full">
left{l}|middle|right{r}|[1]
[1]    |      |[1]
</div>
  
<div data-field="left" class="left"><slot name="left"/></div>
<div data-field="right" class="right"><slot name="right"/></div>
<div data-field="middle" class="w-full box-border bg-surface-50 bg-opacity-60 lg:max-w-maximal relative">
    <Menu></Menu>
    <slot name="main"></slot>
</div>

<style>
img {
    width: 10rem;
    height: 10rem;
}

.blink-me {
    animation: blinker 2s linear infinite;
}

#splash {
    width: 100%;
    height: 100%;
    background-color: rgb(var(--color-surface-50));
}

:global(#splash.hidden) {
    transition: opacity 250ms ease-in; /*, visibility 0ms ease-in 250ms, z-index 0ms ease-in 0ms;*/
    opacity: 0;
    display: flex;
}

@keyframes blinker {
    50% {
        opacity: 0;
    }
}
</style>

<script lang="coffee">
import Menu from './Menu.svelte'
</script>