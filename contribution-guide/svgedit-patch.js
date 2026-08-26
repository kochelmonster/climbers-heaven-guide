// Runtime patch for the CDN-backed SVG-Edit wrapper.
export function applySvgEditPatch(svgEditor) {
  const topo = new URL(location).searchParams.get('url')
  const topoName = topo ? decodeURIComponent(topo.split('/').pop() || '') : ''

  const applyTitle = () => {
    if (!topoName) return
    // Keep both the saved file name and the panel title aligned to the sector topo file.
    svgEditor.title = topoName
    svgEditor.topPanel?.updateTitle?.(topoName)
    svgEditor.svgCanvas?.setDocumentTitle?.(topoName.replace(/\.svg$/i, ''))
  }

  const applyPathDefaults = () => {
    const canvas = svgEditor.svgCanvas
    if (!canvas) return

    if (typeof canvas.setCurProperties === 'function') {
      canvas.setCurProperties('fill', 'none')
      canvas.setCurProperties('fill_opacity', 1)
      canvas.setCurProperties('fill_paint', { type: 'solidColor' })
      canvas.setCurProperties('stroke', '#ff0000')
      canvas.setCurProperties('stroke_opacity', 1)
      canvas.setCurProperties('stroke_width', 2)
      canvas.setCurProperties('stroke_paint', { type: 'solidColor' })
    } else {
      canvas.setColor?.('fill', 'none', true)
      canvas.setColor?.('stroke', '#ff0000', true)
      canvas.setStrokeWidth?.(2)
      canvas.setPaintOpacity?.('stroke', 1, true)
    }

    canvas.setSegType?.(4)
  }

  const enforceStraightSegments = () => {
    const canvas = svgEditor.svgCanvas
    if (!canvas) return

    if (!canvas._straightSegDefaultPatched) {
      const setSegType = canvas.setSegType?.bind(canvas)
      if (setSegType) {
        canvas.setSegType = function (newType) {
          setSegType(newType || 4)
        }
        canvas._straightSegDefaultPatched = true
      }
    }

    const pathActions = canvas.pathActions
    if (pathActions && !pathActions._straightSegDefaultPatched) {
      const setActionSegType = pathActions.setSegType?.bind(pathActions)
      if (typeof setActionSegType === 'function') {
        pathActions.setSegType = function (newType) {
          setActionSegType(newType || 4)
        }
        pathActions._straightSegDefaultPatched = true
      }
    }

    // Path grips call path.setSegType() directly, so patch that prototype too.
    const path = canvas.getPathObj?.()
    const prototype = path && Object.getPrototypeOf(path)
    if (prototype && !prototype._straightSegDefaultPatched) {
      const setPathSegType = prototype.setSegType
      if (typeof setPathSegType === 'function') {
        prototype.setSegType = function (newType) {
          setPathSegType.call(this, newType || 4)
        }
        prototype._straightSegDefaultPatched = true
      }
    }
  }

  const enforceTopoTitle = () => {
    if (!topoName) return
    const panel = svgEditor.topPanel
    if (!panel || panel._topoTitlePatched) return
    const updateTitle = panel.updateTitle?.bind(panel)
    if (typeof updateTitle !== 'function') return
    panel.updateTitle = function (title) {
      const nextTitle = (!title || /^untitled\.svg$/i.test(title)) ? topoName : title
      updateTitle(nextTitle)
      svgEditor.title = nextTitle
    }
    panel._topoTitlePatched = true
  }

  // Set title before init so startup UI picks it up.
  applyTitle()

  // Preserve legacy behavior: forcing node double-click conversion to straight segments.
  document.addEventListener('dblclick', () => {
    const path = svgEditor.svgCanvas?.getPathObj?.()
    const prototype = path && Object.getPrototypeOf(path)
    if (!prototype || prototype._straightSegDefaultPatched) return
    const setSegType = prototype.setSegType
    if (typeof setSegType !== 'function') return
    prototype.setSegType = function (newType) {
      setSegType.call(this, newType || 4)
    }
    prototype._straightSegDefaultPatched = true
  }, true)

  // Re-apply after async startup and topo loading.
  svgEditor.ready(() => {
    enforceTopoTitle()
    applyTitle()
    applyPathDefaults()
    enforceStraightSegments()
    document.addEventListener('mousedown', () => {
      enforceStraightSegments()
    }, true)
    document.addEventListener('mouseup', () => {
      applyPathDefaults()
      enforceStraightSegments()
    }, true)
    document.addEventListener('modeChange', () => {
      applyPathDefaults()
      enforceStraightSegments()
      applyTitle()
    })
    document.addEventListener('click', (event) => {
      const id = event.target?.id
      if (id === 'tool_save' || id === 'tool_save_as') {
        applyTitle()
      }
    }, true)
  })

  svgEditor.init()
}
