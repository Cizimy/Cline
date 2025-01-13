import asyncio
import json
import os
import sys
from pathlib import Path
import sqlite3
from typing import Any, Dict

def format_json(obj: Dict) -> str:
    """JSONを正しい形式でフォーマットする"""
    # 一度JSON文字列に変換
    json_str = json.dumps(obj, separators=(',', ':'))
    # 文字列を解析して正しい形式であることを確認
    json.loads(json_str)
    return json_str + "\n"

class SQLiteServer:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)

    async def handle_request(self, request_str: str) -> str:
        try:
            request = json.loads(request_str)
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")

            if method == "list_tools":
                response = self.list_tools()
            elif method == "call_tool":
                response = await self.call_tool(params)
            else:
                response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    },
                    "id": request_id
                }

            # IDを追加
            if isinstance(response, dict) and "id" not in response:
                response["jsonrpc"] = "2.0"
                response["id"] = request_id

            return format_json(response)
        except Exception as e:
            return format_json({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": str(e)
                },
                "id": None
            })

    def list_tools(self) -> Dict:
        return {
            "jsonrpc": "2.0",
            "result": {
                "tools": [
                    {
                        "name": "read_query",
                        "description": "Execute a read-only SQL query",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"},
                            },
                            "required": ["query"],
                        },
                    },
                    {
                        "name": "write_query",
                        "description": "Execute a SQL query that modifies the database",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"},
                            },
                            "required": ["query"],
                        },
                    },
                ]
            }
        }

    async def call_tool(self, params: Dict) -> Dict:
        tool_name = params.get("name")
        args = params.get("arguments", {})

        if tool_name not in ["read_query", "write_query"]:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"Unknown tool: {tool_name}"
                }
            }

        if "query" not in args:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32602,
                    "message": "Query parameter is required"
                }
            }

        try:
            cursor = self.conn.cursor()
            if tool_name == "read_query":
                cursor.execute(args["query"])
                rows = cursor.fetchall()
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": str(rows),
                            }
                        ]
                    }
                }
            else:  # write_query
                cursor.execute(args["query"])
                self.conn.commit()
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Query executed successfully. Rows affected: {cursor.rowcount}",
                            }
                        ]
                    }
                }
        except sqlite3.Error as e:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32000,
                    "message": f"SQLite error: {str(e)}"
                }
            }

async def run_server():
    # データベースのパスを環境変数から取得
    db_path = os.environ.get(
        "SQLITE_DB_PATH",
        str(Path.home() / ".local" / "share" / "mcp" / "sqlite" / "db.sqlite")
    )

    # データベースのディレクトリを作成
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    # サーバーインスタンスを作成
    server = SQLiteServer(db_path)

    # 初期化メッセージを送信
    init_message = {
        "jsonrpc": "2.0",
        "result": {
            "name": "sqlite-server",
            "version": "0.1.0",
            "capabilities": {
                "tools": True
            }
        },
        "id": 0
    }
    sys.stdout.buffer.write(format_json(init_message).encode('utf-8'))
    sys.stdout.buffer.flush()

    # 標準入出力を使用してJSONベースの通信を行う
    while True:
        try:
            # 非同期で標準入力を読み込む
            request_str = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not request_str:
                break

            # リクエストを処理して応答を生成
            response_str = await server.handle_request(request_str)

            # バイナリモードで応答を書き込む
            sys.stdout.buffer.write(response_str.encode('utf-8'))
            sys.stdout.buffer.flush()

        except Exception as e:
            # エラーが発生した場合はエラーレスポンスを返す
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                },
                "id": None
            }
            sys.stdout.buffer.write(format_json(error_response).encode('utf-8'))
            sys.stdout.buffer.flush()

if __name__ == "__main__":
    asyncio.run(run_server())