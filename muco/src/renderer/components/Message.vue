<script setup>
import { ref, computed } from 'vue';
import { config } from '@/renderer/store/config'
import { renderMarkdownSafe, renderMarkdown } from '@/renderer/utils/markdown';

let currentTheme = computed(() =>config.data.themes[config.data.activeTheme]);
let authorTheme = computed(() => `
  background: ${currentTheme.value.message.author.background};
  color: ${currentTheme.value.message.author.textcolor};
  font-family: ${currentTheme.value.message.author.font};
  font-size: ${currentTheme.value.message.author.fontsize};
  font-weight: ${currentTheme.value.message.author.fontboldness};
`)
let contentTheme = computed(() => `
  background: ${currentTheme.value.message.content.background};
  color: ${currentTheme.value.message.content.textcolor};
  font-family: ${currentTheme.value.message.content.font};
  font-size: ${currentTheme.value.message.content.fontsize};
  font-weight: ${currentTheme.value.message.content.fontboldness};
`)

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
});
let message = props.message;
let renderedAuthor;
let renderedContent;
if (config.data.safeFormattingRender) {
  renderedAuthor = ref(renderMarkdownSafe(message.author));
  renderedContent = ref(renderMarkdownSafe(message.text));
} else {
  renderedAuthor = ref(renderMarkdown(message.author));
  renderedContent = ref(renderMarkdown(message.text));
}

</script>

<template>
  <div class="message" ref="thisRef">
    <div class="author" :style="authorTheme" v-html="renderedAuthor"></div>
    <div class="author slicer" :style="authorTheme">: </div>
    <div class="content" :style="contentTheme" v-html="renderedContent"></div>
  </div>
</template>

<style>

.message {
  display: flex;
  flex-direction: row;
  margin-bottom: 1px;
  height: auto;
}

.author {
  user-select: none;
}

.content {
  overflow-wrap: break-word;
  white-space: pre-wrap;
  word-break: keep-all;
  line-break: strict;
  hyphens: auto;
  width: 87%;
  -webkit-app-region: no-drag;
}

.content p {
  margin: 0;
  display: inline;
  line-height: 1;
}

.author p {
  margin: 0;
  display: inline;
  line-height: 1;
}

.content img {
  max-width: 60vw;
  max-height: 70vh;
}

.content video {
  max-width: 60vw;
  max-height: 70vh;
}

.slicer {
  margin-right: 4px;
}

</style>
