const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  pages: {
    index: {
      entry: 'src/renderer/main.js',
      template: 'public/index.html',
      filename: 'index.html'
    }
  },
  transpileDependencies: true,
  lintOnSave: false, // dev
  pluginOptions: {
    electronBuilder: {
      mainProcessFile: 'src/main/background.js',
      preload: 'src/main/preload.js'
    }
  }
})
