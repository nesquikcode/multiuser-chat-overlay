const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  lintOnSave: false, // dev
  pluginOptions: {
    electronBuilder: {
      preload: 'src/preload.js'
    }
  }
})
