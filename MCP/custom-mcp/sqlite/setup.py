from setuptools import setup, find_packages

setup(
    name="mcp-server-sqlite",
    version="0.6.2",
    description="A simple SQLite MCP server",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "mcp>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "mcp-server-sqlite=mcp_server_sqlite:main",
        ],
    },
)
