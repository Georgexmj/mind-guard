const fs = require('fs')
const path = require('path')

const distDir = path.resolve(__dirname, '..', 'dist', 'build', 'mp-weixin')
const target = path.join(distDir, 'project.config.json')

if (!fs.existsSync(distDir)) {
  console.log('[fix-mp-config] dist folder not found, skip.')
  process.exit(0)
}

const config = {
  description: 'Mini Program project config',
  packOptions: {
    ignore: [],
  },
  setting: {
    urlCheck: false,
    es6: true,
    postcss: false,
    minified: false,
    newFeature: true,
    bigPackageSizeSupport: true,
  },
  compileType: 'miniprogram',
  libVersion: '',
  appid: 'wx64963c60bee4f79c',
  projectname: 'MindGuardCognitive',
  condition: {
    search: { current: -1, list: [] },
    conversation: { current: -1, list: [] },
    game: { current: -1, list: [] },
    miniprogram: { current: -1, list: [] },
  },
}

fs.writeFileSync(target, `${JSON.stringify(config, null, 2)}\n`, 'utf8')
console.log('[fix-mp-config] project.config.json fixed.')
