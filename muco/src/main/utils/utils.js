export function normalizeKey(key) {
    const map = {
        Space: 'Space',
        Esc: 'Escape',
        Enter: 'Enter',
        Tab: 'Tab',
        Up: 'ArrowUp',
        Down: 'ArrowDown',
        Left: 'ArrowLeft',
        Right: 'ArrowRight'
    }

    if (map[key]) return map[key]

    if (key.length === 1) return key.toUpperCase()

    return key
}

export function parseAccelerator(accelerator) {
  const parts = accelerator.split('+')

  const modifiers = []
  let key = null

  for (const part of parts) {
    switch (part.toLowerCase()) {
      case 'ctrl':
      case 'control':
      case 'commandorcontrol':
        modifiers.push('control')
        break
      case 'shift':
        modifiers.push('shift')
        break
      case 'alt':
      case 'option':
        modifiers.push('alt')
        break
      case 'cmd':
      case 'command':
      case 'meta':
        modifiers.push('meta')
        break
      default:
        key = normalizeKey(part)
    }
  }

  return { key, modifiers }
}

export function sendTransparentKey(win, accelerator) {
  const { key, modifiers } = parseAccelerator(accelerator)

  if (!key) return

  win.webContents.sendInputEvent({
    type: 'keyDown',
    keyCode: key,
    modifiers
  })

  if (key.length === 1 || key === 'Space') {
    win.webContents.sendInputEvent({
      type: 'char',
      keyCode: key,
      modifiers
    })
  }

  win.webContents.sendInputEvent({
    type: 'keyUp',
    keyCode: key,
    modifiers
  })
}
