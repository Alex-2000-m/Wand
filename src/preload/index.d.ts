import { ElectronAPI } from '@electron-toolkit/preload'

declare global {
  interface Window {
    electron: ElectronAPI
    api: {
      chat: (message: string, config?: any) => Promise<string>
      fetchModels: (config: any) => Promise<any>
      chatStream: (message: string, config: any, onChunk: (chunk: string) => void, onDone: () => void, onError: (error: string) => void) => () => void
      chatStop: () => void
      openDirectory: () => Promise<string | null>
      openFile: () => Promise<string | null>
      showSaveDialog: () => Promise<string | null>
      readDirectory: (path: string) => Promise<Array<{ name: string; isDirectory: boolean; path: string }>>
      readFile: (path: string) => Promise<string>
      saveFile: (path: string, content: string) => Promise<void>
      showOpenDialog: () => Promise<string[] | null>
    }
  }
}
