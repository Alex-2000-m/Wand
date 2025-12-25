import { ipcMain } from 'electron';
import { spawn, ChildProcess } from 'child_process';
import path from 'path';

// This simulates the AI service that would connect to OpenAI/Anthropic/Local LLMs
export class AIService {
  private currentProcess: ChildProcess | null = null;

  constructor() {
    this.setupHandlers();
  }

  // Resolve Python backend entry; works in dev and in packaged app
  private getBackendScriptPath() {
    if (process.env.NODE_ENV === 'development') {
      return path.join(process.cwd(), 'src', 'backend', 'cli.py');
    }
    return path.join(process.resourcesPath, 'backend', 'cli.py');
  }

  private setupHandlers() {
    ipcMain.on('ai:chat-stream', (event, { message, history, config }) => {
      this.processMessageStream(event, message, history, config);
    });

    ipcMain.on('ai:chat-stop', (event) => {
      if (this.currentProcess) {
        this.currentProcess.kill();
        this.currentProcess = null;
        event.reply('ai:chat-done'); // Notify frontend that it's done (stopped)
      }
    });

    ipcMain.handle('ai:fetch-models', async (event, config) => {
      return this.fetchModels(config);
    });

    ipcMain.handle('ai:get-tools', async (event, config) => {
      return this.getTools(config);
    });

    ipcMain.handle('ai:clear-temp-tools', async (event) => {
      return this.clearTempTools();
    });

    ipcMain.handle('ai:save-tool', async (event, name, code, description) => {
      return this.saveTool(name, code, description);
    });
  }

  private saveTool(name: string, code: string, description: string): Promise<any> {
    return new Promise((resolve, reject) => {
      const scriptPath = this.getBackendScriptPath();
      const pythonProcess = spawn('python', [scriptPath]);

      const inputData = JSON.stringify({ 
        type: 'save_tool', 
        config: {}, 
        tool_data: { name, code, description } 
      });
      pythonProcess.stdin.write(inputData);
      pythonProcess.stdin.end();

      let outputData = '';
      pythonProcess.stdout.on('data', (data) => { outputData += data.toString(); });
      
      pythonProcess.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`Python script exited with code ${code}`));
        } else {
          try {
            resolve(JSON.parse(outputData));
          } catch (e) {
            reject(new Error(`Failed to parse output: ${outputData}`));
          }
        }
      });
    });
  }

  private clearTempTools(): Promise<any> {
    return new Promise((resolve, reject) => {
      const scriptPath = this.getBackendScriptPath();
      const pythonProcess = spawn('python', [scriptPath]);

      const inputData = JSON.stringify({ type: 'clear_temp_tools', config: {} });
      pythonProcess.stdin.write(inputData);
      pythonProcess.stdin.end();

      let outputData = '';
      pythonProcess.stdout.on('data', (data) => { outputData += data.toString(); });
      
      pythonProcess.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`Python script exited with code ${code}`));
        } else {
          resolve(JSON.parse(outputData));
        }
      });
    });
  }

  private getTools(config: any): Promise<any> {
    return new Promise((resolve, reject) => {
      console.log('Fetching tools via Python CLI');
      const scriptPath = this.getBackendScriptPath();
      const pythonProcess = spawn('python', [scriptPath]);

      const inputData = JSON.stringify({ type: 'get_tools', config });
      pythonProcess.stdin.write(inputData);
      pythonProcess.stdin.end();

      let outputData = '';
      let errorData = '';

      pythonProcess.stdout.on('data', (data) => {
        outputData += data.toString();
      });

      pythonProcess.stderr.on('data', (data) => {
        errorData += data.toString();
      });

      pythonProcess.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`Python script exited with code ${code}: ${errorData}`));
          return;
        }
        try {
          const result = JSON.parse(outputData);
          if (result.error) {
            reject(new Error(result.error));
          } else {
            resolve(result.tools);
          }
        } catch (e) {
          reject(new Error(`Failed to parse Python output: ${outputData}`));
        }
      });
    });
  }

  private fetchModels(config: any): Promise<any> {
    return new Promise((resolve, reject) => {
      console.log('Fetching models via Python CLI');
      const scriptPath = this.getBackendScriptPath();
      const pythonProcess = spawn('python', [scriptPath]);

      const inputData = JSON.stringify({ type: 'fetch_models', config });
      pythonProcess.stdin.write(inputData);
      pythonProcess.stdin.end();

      let outputData = '';
      let errorData = '';

      pythonProcess.stdout.on('data', (data) => {
        outputData += data.toString();
      });

      pythonProcess.stderr.on('data', (data) => {
        errorData += data.toString();
      });

      pythonProcess.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`Python script exited with code ${code}: ${errorData}`));
          return;
        }
        try {
          const result = JSON.parse(outputData);
          if (result.error) {
            reject(new Error(result.error));
          } else {
            resolve(result.models);
          }
        } catch (e) {
          reject(new Error(`Failed to parse Python output: ${outputData}`));
        }
      });
    });
  }

  private processMessageStream(event: Electron.IpcMainEvent, message: string, history: any[], config: any) {
    console.log('Processing AI request via Python CLI (Stream):', message);
    
    // Kill any existing process
    if (this.currentProcess) {
      this.currentProcess.kill();
      this.currentProcess = null;
    }

    const scriptPath = this.getBackendScriptPath();
    const pythonProcess = spawn('python', [scriptPath]);
    this.currentProcess = pythonProcess;

    // Send data to Python script via stdin
    const inputData = JSON.stringify({ message, history, config });
    pythonProcess.stdin.write(inputData);
    pythonProcess.stdin.end();

    // Collect output from stdout
    pythonProcess.stdout.on('data', (data) => {
      const lines = data.toString().split('\n');
      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const result = JSON.parse(line);
          if (result.error) {
            event.reply('ai:chat-error', result.error);
          } else if (result.chunk) {
            event.reply('ai:chat-chunk', result.chunk);
          }
        } catch (e) {
          console.error('Failed to parse Python output chunk:', line);
        }
      }
    });

    // Collect error from stderr
    pythonProcess.stderr.on('data', (data) => {
      console.error('Python stderr:', data.toString());
    });

    pythonProcess.on('close', (code) => {
      if (this.currentProcess === pythonProcess) {
        this.currentProcess = null;
      }
      if (code !== 0 && code !== null) { // code is null if killed
        event.reply('ai:chat-error', `Python script exited with code ${code}`);
      }
      event.reply('ai:chat-done');
    });

    pythonProcess.on('error', (err) => {
      event.reply('ai:chat-error', `Failed to start Python process: ${err.message}`);
    });
  }
}
