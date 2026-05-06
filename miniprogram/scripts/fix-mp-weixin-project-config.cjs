const fs = require('fs')
const path = require('path')

const distDir = path.resolve(__dirname, '..', 'dist', 'build', 'mp-weixin')
const target = path.join(distDir, 'project.config.json')
const appWxss = path.join(distDir, 'app.wxss')
const appJson = path.join(distDir, 'app.json')

if (!fs.existsSync(distDir)) {
  console.log('[fix-mp-config] dist folder not found, skip.')
  process.exit(0)
}

let existing = {}
if (fs.existsSync(target)) {
  try {
    existing = JSON.parse(fs.readFileSync(target, 'utf8'))
  } catch (error) {
    console.warn('[fix-mp-config] project.config.json parse failed, fallback to defaults.', error?.message || error)
  }
}

const config = {
  ...existing,
  description: existing.description || 'Mini Program project config',
  compileType: 'miniprogram',
  appid: existing.appid || 'wx64963c60bee4f79c',
  projectname: existing.projectname || 'MindGuardCognitive',
  miniprogramRoot: '.',
  srcMiniprogramRoot: '.',
  libVersion: existing.libVersion || 'trial',
  packOptions: {
    ignore: Array.isArray(existing?.packOptions?.ignore) ? existing.packOptions.ignore : [],
    include: Array.isArray(existing?.packOptions?.include) ? existing.packOptions.include : [],
  },
  setting: {
    ...existing.setting,
    urlCheck: false,
    es6: true,
    postcss: false,
    minified: false,
    newFeature: true,
    bigPackageSizeSupport: true,
  },
  condition: {
    search: { current: -1, list: [] },
    conversation: { current: -1, list: [] },
    game: { current: -1, list: [] },
    miniprogram: { current: -1, list: [] },
  },
}

fs.writeFileSync(target, `${JSON.stringify(config, null, 2)}\n`, 'utf8')
console.log('[fix-mp-config] project.config.json merged and fixed.')

if (fs.existsSync(appJson)) {
  try {
    const appConfig = JSON.parse(fs.readFileSync(appJson, 'utf8'))
    // app.json `permission` does not support scope.record/scope.camera in current WeChat toolchain.
    if (appConfig && appConfig.permission) {
      delete appConfig.permission
      fs.writeFileSync(appJson, `${JSON.stringify(appConfig, null, 2)}\n`, 'utf8')
      console.log('[fix-mp-config] app.json invalid permission removed.')
    }
  } catch (error) {
    console.warn('[fix-mp-config] app.json parse failed, skip permission cleanup.', error?.message || error)
  }
}

if (fs.existsSync(appWxss)) {
  const source = fs.readFileSync(appWxss, 'utf8')
  const fixed = source.replace(/\[data-c-h="true"\]\{display:\s*none\s*!important;\}/g, '')

  if (fixed !== source) {
    fs.writeFileSync(appWxss, fixed, 'utf8')
    console.log('[fix-mp-config] app.wxss hidden-node rule removed.')
  }
}
