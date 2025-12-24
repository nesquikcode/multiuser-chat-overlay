import { ipc } from '@/services/ipc'

function filePathToUrl(filePath) {
  return new URL(`file://${filePath}`).href
}

export async function loadFonts() {
  const fonts = await ipc.getFonts();

  for (const font of fonts) {
    const url = filePathToUrl(font.path)

    const fontFace = new FontFace(
      font.name,
      `url("${url}")`
    )

    await fontFace.load()
    document.fonts.add(fontFace)
  }
}
