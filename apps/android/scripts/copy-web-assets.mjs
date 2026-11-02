import { cp, mkdir, rm } from 'node:fs/promises'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = resolve(fileURLToPath(new URL('.', import.meta.url)))
const androidRoot = resolve(here, '..')
const source = resolve(androidRoot, '..', 'web', 'dist')
const destination = resolve(androidRoot, 'web-assets')

await rm(destination, { recursive: true, force: true })
await mkdir(destination, { recursive: true })
await cp(source, destination, { recursive: true })
console.log(`Copied web build from ${source} to ${destination}`)
