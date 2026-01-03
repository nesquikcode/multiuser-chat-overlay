import { marked } from 'marked'
import DOMPurify from 'dompurify'

marked.setOptions({
  breaks: true,
  gfm: true
})

export function renderMarkdown(text) {
  return marked.parse(text)
}

export function renderMarkdownSafe(text) {
  return DOMPurify.sanitize(marked.parse(text))
}