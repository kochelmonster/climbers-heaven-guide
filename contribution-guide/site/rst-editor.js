const params = new URLSearchParams(location.search)
const fallback = document.getElementById('fallback')
const status = document.getElementById('status')
const heading = document.getElementById('filename')
const githubRawBase = 'https://raw.githubusercontent.com/kochelmonster/climbers-heaven-guide/develop/docutil'

let directives = {}
let getValue = () => fallback.value

const fail = (message) => {
  status.textContent = message
  status.className = 'error'
}

const encodePath = (path) => path.split('/').map(encodeURIComponent).join('/')

// Only files listed in the index may be fetched, so ?file= cannot escape docutil/.
const resolveFile = async () => {
  const wanted = params.get('file')
  const response = await fetch('../data/files.json')
  const sectors = await response.json()
  return sectors.find((sector) => sector.rst === wanted)
}

const directiveAt = (lines, index) => {
  for (let i = index; i >= 0 && i > index - 60; i--) {
    const line = lines[i]
    const directive = /^\s*\.\.\s+([\w-]+)::/.exec(line)
    if (directive) return directives[directive[1]] ? directive[1] : null
    if (!/^\s*:[\w-]+:/.test(line)) return null
  }
  return null
}

const complete = (context) => {
  const line = context.state.doc.lineAt(context.pos)
  const before = line.text.slice(0, context.pos - line.from)
  const lines = []
  for (let i = 1; i < line.number; i++) lines.push(context.state.doc.line(i).text)

  const name = /^\s*\.\.\s+([\w-]*)$/.exec(before)
  if (name) {
    return {
      from: context.pos - name[1].length,
      options: Object.entries(directives).map(([label, spec]) => ({
        label,
        type: 'keyword',
        info: spec.doc,
        apply: `${label}:: `
      }))
    }
  }

  const current = directiveAt(lines, lines.length - 1)
  if (!current) return null
  const spec = directives[current]

  const value = /^\s*:([\w-]+):\s*([\w+ -]*)$/.exec(before)
  if (value) {
    const values = spec.options[value[1]]?.values ?? []
    if (!values.length) return null
    return {
      from: context.pos - value[2].length,
      options: values.map((label) => ({ label, type: 'enum' }))
    }
  }

  const option = /^\s*:([\w-]*)$/.exec(before)
  if (option) {
    return {
      from: context.pos - option[1].length,
      options: Object.entries(spec.options).map(([label, info]) => ({
        label,
        type: 'property',
        info: info.doc,
        apply: `${label}: `
      }))
    }
  }
  return null
}

const HEADING = /^([=\-~*^"'`#+_:.])\1{1,}\s*$/

// @codemirror/legacy-modes has no reStructuredText mode, so highlight the subset the guide uses.
const rstMode = {
  name: 'rst',
  startState: () => ({ kind: null }),
  token (stream, state) {
    if (stream.sol()) {
      state.kind = null
      if (HEADING.test(stream.string)) {
        stream.skipToEnd()
        return 'heading'
      }
      if (stream.match(/^\s*\.\.\s+[\w-]+::/, false)) state.kind = 'directive'
      else if (stream.match(/^\s*\.\.\s+_/, false)) state.kind = 'target'
      else if (stream.match(/^\s*\.\.(\s|$)/, false)) {
        stream.skipToEnd()
        return 'comment'
      } else if (stream.match(/^\s*:[\w-]+:/, false)) state.kind = 'option'
    }

    switch (state.kind) {
      case 'directive':
        if (stream.match(/^\s*\.\.\s+/)) return 'marker'
        if (stream.match(/^[\w-]+(?=::)/)) {
          state.kind = 'directive-end'
          return 'directive'
        }
        break
      case 'directive-end':
        if (stream.match(/^::/)) {
          state.kind = 'argument'
          return 'marker'
        }
        break
      case 'argument':
        stream.skipToEnd()
        return 'argument'
      case 'target':
        stream.skipToEnd()
        return 'target'
      case 'option':
        if (stream.match(/^\s*:[\w-]+:/)) {
          state.kind = 'value'
          return 'option'
        }
        break
      case 'value':
        stream.skipToEnd()
        return 'value'
    }

    if (stream.match(/^``[^`]*``/)) return 'literal'
    if (stream.match(/^`[^`]*`__?/)) return 'link'
    if (stream.match(/^https?:\/\/\S+/)) return 'link'
    if (stream.match(/^\*\*[^*]+\*\*/)) return 'strong'
    if (stream.match(/^\*[^*]+\*/)) return 'emphasis'
    stream.next()
    return null
  }
}

const mountCodeMirror = async (text) => {
  const { EditorView, basicSetup } = await import('codemirror')
  const { keymap } = await import('@codemirror/view')
  const { indentWithTab } = await import('@codemirror/commands')
  const { StreamLanguage } = await import('@codemirror/language')
  const { autocompletion } = await import('@codemirror/autocomplete')
  const { tags } = await import('@lezer/highlight')

  const language = StreamLanguage.define({
    ...rstMode,
    tokenTable: {
      heading: tags.heading,
      marker: tags.meta,
      directive: tags.keyword,
      argument: tags.string,
      option: tags.propertyName,
      value: tags.atom,
      target: tags.labelName,
      literal: tags.monospace,
      link: tags.link,
      strong: tags.strong,
      emphasis: tags.emphasis
    }
  })

  const view = new EditorView({
    doc: text,
    parent: document.getElementById('editor'),
    extensions: [
      basicSetup,
      keymap.of([indentWithTab]),
      language,
      EditorView.lineWrapping,
      autocompletion({ override: [complete], activateOnTyping: true })
    ]
  })
  fallback.remove()
  getValue = () => view.state.doc.toString()
}

const start = async () => {
  const sector = await resolveFile()
  if (!sector) {
    fail('Unknown file. Please pick a sector from the index.')
    fallback.disabled = true
    return
  }

  heading.textContent = `${sector.title} — ${sector.rst}`
  document.title = `${sector.rst} — Climbers Heaven Guide`
  const [text, meta] = await Promise.all([
    fetch(`${githubRawBase}/${encodePath(sector.rst)}`).then((r) => {
      if (!r.ok) throw new Error(`GitHub returned ${r.status}`)
      return r.text()
    }),
    fetch('../data/directives.json').then((r) => r.json())
  ])
  directives = meta
  fallback.value = text

  try {
    await mountCodeMirror(text)
  } catch (error) {
    fail('Syntax highlighting unavailable offline — editing as plain text.')
    console.warn(error)
  }

  document.getElementById('download').addEventListener('click', () => {
    const url = URL.createObjectURL(new Blob([getValue()], { type: 'text/plain' }))
    const link = document.createElement('a')
    link.href = url
    link.download = sector.rst.split('/').pop()
    document.body.append(link)
    link.click()
    // Revoking straight away cancels the download in some browsers.
    setTimeout(() => {
      link.remove()
      URL.revokeObjectURL(url)
    }, 1000)
  })

  document.getElementById('copy').addEventListener('click', async () => {
    await navigator.clipboard.writeText(getValue())
    status.textContent = 'Copied.'
  })
}

start().catch((error) => {
  fail(`Could not load the file: ${error.message}`)
})
