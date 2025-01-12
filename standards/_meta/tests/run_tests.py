#!/usr/bin/env python3
import os
import sys
import subprocess
import asyncio
from datetime import datetime
from typing import List, Dict, Any

class TestRunner:
    def __init__(self, meta_dir: str):
        self.meta_dir = meta_dir
        self.test_results: List[Dict[str, Any]] = []

    async def run_test(self, script_name: str, description: str) -> bool:
        """個別のテストスクリプトを実行"""
        print(f"\n実行中: {description}...")
        
        try:
            script_path = os.path.join(os.path.dirname(__file__), script_name)
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                script_path,
                self.meta_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            stdout, stderr = await process.communicate()
            
            success = process.returncode == 0
            self.test_results.append({
                "name": script_name,
                "description": description,
                "success": success,
                "output": stdout.decode() if stdout else "",
                "error": stderr.decode() if stderr else ""
            })

            if success:
                print(f"✓ {description} - 成功")
            else:
                print(f"✗ {description} - 失敗")
                if stderr:
                    print(f"エラー出力:\n{stderr.decode()}")

            return success

        except Exception as e:
            print(f"✗ {description} - エラー: {str(e)}")
            self.test_results.append({
                "name": script_name,
                "description": description,
                "success": False,
                "error": str(e)
            })
            return False

    def generate_summary_report(self) -> str:
        """テスト結果のサマリーレポートを生成"""
        report = []
        report.append("# テスト実行サマリー")
        report.append(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r["success"])
        
        report.append(f"\n## 実行結果")
        report.append(f"- 総テスト数: {total_tests}")
        report.append(f"- 成功: {successful_tests}")
        report.append(f"- 失敗: {total_tests - successful_tests}")
        
        report.append("\n## 詳細結果")
        for result in self.test_results:
            status = "✓" if result["success"] else "✗"
            report.append(f"\n### {status} {result['description']}")
            if not result["success"] and result.get("error"):
                report.append(f"エラー:\n```\n{result['error']}\n```")

        # 個別のテストレポートへのリンク
        report.append("\n## 詳細レポート")
        report.append("- [スキーマ検証レポート](validation_report.md)")
        report.append("- [非同期処理・パフォーマンステストレポート](async_performance_report.md)")
        report.append("- [セキュリティテストレポート](security_report.md)")

        return "\n".join(report)

async def main():
    if len(sys.argv) != 2:
        print("使用方法: python run_tests.py <path_to_meta_dir>")
        sys.exit(1)

    meta_dir = sys.argv[1]
    runner = TestRunner(meta_dir)
    
    # テストの実行
    tests = [
        ("validate_schemas.py", "スキーマ検証"),
        ("test_async_performance.py", "非同期処理・パフォーマンステスト"),
        ("test_security.py", "セキュリティテスト")
    ]

    results = []
    for script, desc in tests:
        success = await runner.run_test(script, desc)
        results.append(success)

    # サマリーレポートの生成と保存
    report = runner.generate_summary_report()
    report_path = os.path.join(meta_dir, "test_summary_report.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\nテスト完了。詳細は {report_path} を参照してください。")
    
    # 全テストが成功した場合のみ終了コード0を返す
    sys.exit(0 if all(results) else 1)

if __name__ == "__main__":
    asyncio.run(main())