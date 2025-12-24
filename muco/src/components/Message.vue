<script setup>
import { ref, computed } from 'vue';
import { config, saveConfig } from '@/store/config'
import { renderMarkdownSafe } from '@/utils/markdown';

let currentTheme = config.data.themes[config.data.activeTheme];
let authorTheme = computed(() => `
  background: ${currentTheme.message.author.background};
  color: ${currentTheme.message.author.textcolor};
  font-family: ${currentTheme.message.author.font};
  font-size: ${currentTheme.message.author.fontsize};
  font-weight: ${currentTheme.message.author.fontboldness};
`)
let contentTheme = computed(() => `
  background: ${currentTheme.message.content.background};
  color: ${currentTheme.message.content.textcolor};
  font-family: ${currentTheme.message.content.font};
  font-size: ${currentTheme.message.content.fontsize};
  font-weight: ${currentTheme.message.content.fontboldness};
`)

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
});
let message = props.message;
let renderedContent = ref(renderMarkdownSafe(message.text));

</script>

<template>
  <div class="message">
    <div class="author" :style="authorTheme">{{ message.author }}: </div>
    <div class="content" :style="contentTheme" v-html="renderedContent"></div>
  </div>
</template>

<style>

.message {
  display: flex;
  flex-direction: row;
  gap: 4px;
  margin-bottom: 1px;
  height: auto;
}

.author {
  user-select: none;
}

.content {
  overflow-wrap: break-word;
  word-break: break-word;
  white-space: pre-wrap;
  word-break: break-all;
  -webkit-app-region: no-drag;
  width: 87%;
}


.content p {
  margin: 0;
  display: inline;
  line-height: 1;
}

</style>
