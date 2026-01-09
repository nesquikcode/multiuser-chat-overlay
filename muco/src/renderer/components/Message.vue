<script setup>
import { ref, computed, compile } from 'vue';
import { config } from '@/renderer/store/config'
import { renderMarkdownSafe, renderMarkdown } from '@/renderer/utils/markdown';

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
});
let message = props.message;
let currentTheme = computed(() => config.data.themes[config.data.activeTheme].message[message.msgType]);
let compiled = computed(() => {return compile(currentTheme.value.messagehtml)})

const MessageContent = {
  setup() {

    let renderedAuthor;
    let renderedContent;
    if (config.data.safeFormattingRender) {
      renderedAuthor = ref(renderMarkdownSafe(message.author));
      renderedContent = ref(renderMarkdownSafe(message.text));
    } else {
      renderedAuthor = ref(renderMarkdown(message.author));
      renderedContent = ref(renderMarkdown(message.text));
    }

    let currentTheme = computed(() => config.data.themes[config.data.activeTheme].message[message.msgType]);
    let authorTheme = computed(() => `
      background: ${currentTheme.value.author.background};
      color: ${currentTheme.value.author.textcolor};
      font-family: ${currentTheme.value.author.font};
      font-size: ${currentTheme.value.author.fontsize};
      font-weight: ${currentTheme.value.author.fontboldness};
    `)
    let contentTheme = computed(() => `
      background: ${currentTheme.value.content.background};
      color: ${currentTheme.value.content.textcolor};
      font-family: ${currentTheme.value.content.font};
      font-size: ${currentTheme.value.content.fontsize};
      font-weight: ${currentTheme.value.content.fontboldness};
    `)


    return {
      currentTheme,
      contentTheme,
      authorTheme,
      renderedAuthor,
      renderedContent,
      config
    }
  },
  props: {},
  data() {
    return {}
  },
  computed: {},
  methods: {},
  render: compiled.value
}

</script>

<template>
  <component :is="MessageContent" ref="thisRef">
  </component>
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
  word-break: break-word;
  line-break: strict;
  hyphens: auto;
  width: auto;
  padding-right: 4px;
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

.content audio {
  max-width: 75vw;
  max-height: 17vh;
}

.slicer {
  margin-right: 4px;
}

</style>
