/**
 * UI Tool Definitions
 * These are tools that execute in the browser and modify the UI
 */

export interface UIToolDefinition {
  type: string;
  name: string;
  description: string;
  parameters: {
    type: string;
    properties: Record<string, any>;
    required: string[];
  };
}

export interface UIToolHandler {
  (args: Record<string, any>): Promise<string> | string;
}

/**
 * Registry of UI tools with their definitions and handlers
 */
export const uiToolRegistry: Record<string, {
  definition: UIToolDefinition;
  handler: UIToolHandler;
}> = {
  change_theme_color: {
    definition: {
      type: "function",
      name: "change_theme_color",
      description: "Changes the UI theme color. Use this when user wants to change colors, theme, or appearance. Available colors: blue, purple, green, red, orange, pink, indigo, teal.",
      parameters: {
        type: "object",
        properties: {
          color: {
            type: "string",
            enum: ["blue", "purple", "green", "red", "orange", "pink", "indigo", "teal"],
            description: "The color to set as theme"
          }
        },
        required: ["color"]
      }
    },
    handler: async (args: Record<string, any>) => {
      // This will be called by the WebSocket hook when backend requests UI tool execution
      const event = new CustomEvent('ui-tool-execute', {
        detail: { tool: 'change_theme_color', args }
      });
      window.dispatchEvent(event);
      return `Theme color changed to ${args.color}`;
    }
  },

  enable_high_contrast: {
    definition: {
      type: "function",
      name: "enable_high_contrast",
      description: "Toggles high contrast mode for better accessibility. Use this when user mentions accessibility, contrast, or visibility issues.",
      parameters: {
        type: "object",
        properties: {
          enabled: {
            type: "boolean",
            description: "True to enable high contrast, False to disable"
          }
        },
        required: ["enabled"]
      }
    },
    handler: async (args: Record<string, any>) => {
      const event = new CustomEvent('ui-tool-execute', {
        detail: { tool: 'enable_high_contrast', args }
      });
      window.dispatchEvent(event);
      return `High contrast mode ${args.enabled ? 'enabled' : 'disabled'}`;
    }
  }
};

/**
 * Get all UI tool definitions to send to backend
 */
export function getUIToolDefinitions(): UIToolDefinition[] {
  return Object.values(uiToolRegistry).map(tool => tool.definition);
}

/**
 * Execute a UI tool by name
 */
export async function executeUITool(toolName: string, args: Record<string, any>): Promise<string> {
  const tool = uiToolRegistry[toolName];
  if (!tool) {
    throw new Error(`UI tool '${toolName}' not found`);
  }
  return await tool.handler(args);
}
