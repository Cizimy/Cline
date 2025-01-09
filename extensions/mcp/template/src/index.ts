import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListResourcesRequestSchema,
  ListResourceTemplatesRequestSchema,
  ListToolsRequestSchema,
  McpError,
  ReadResourceRequestSchema,
  ServerResponse,
} from '@modelcontextprotocol/sdk/types.js';

class TemplateServer {
  private server: Server;

  constructor() {
    this.server = new Server(
      {
        name: 'template-server',
        version: '0.1.0',
      },
      {
        capabilities: {
          resources: {},
          tools: {},
        },
      }
    );

    this.setupHandlers();

    this.server.onerror = (error: Error): void => {
      console.error('[MCP Error]', error);
    };

    process.on('SIGINT', async (): Promise<void> => {
      await this.server.close();
      process.exit(0);
    });
  }

  private setupHandlers(): void {
    this.server.setRequestHandler(
      ListResourcesRequestSchema,
      async (): Promise<ServerResponse> => ({
        resources: [],
      })
    );

    this.server.setRequestHandler(
      ListResourceTemplatesRequestSchema,
      async (): Promise<ServerResponse> => ({
        resourceTemplates: [],
      })
    );

    this.server.setRequestHandler(
      ReadResourceRequestSchema,
      async (request): Promise<ServerResponse> => {
        throw new McpError(
          ErrorCode.InvalidRequest,
          `Invalid URI format: ${request.params.uri}`
        );
      }
    );

    this.server.setRequestHandler(
      ListToolsRequestSchema,
      async (): Promise<ServerResponse> => ({
        tools: [],
      })
    );

    this.server.setRequestHandler(
      CallToolRequestSchema,
      async (request): Promise<ServerResponse> => {
        throw new McpError(
          ErrorCode.MethodNotFound,
          `Unknown tool: ${request.params.name}`
        );
      }
    );
  }

  public async run(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Template MCP server running on stdio');
  }
}

const server = new TemplateServer();
server.run().catch((error: Error) => {
  console.error('Server error:', error);
  process.exit(1);
});
