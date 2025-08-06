import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfutils
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import os

def setup_japanese_font():
    """日本語フォントをセットアップ"""
    import platform
    
    font_paths = []
    system = platform.system()
    
    # プロジェクト内のfontsディレクトリもチェック
    local_font_paths = [
        "./fonts/NotoSansCJK-jp-Regular.otf",
        "./fonts/NotoSansCJK-Regular.ttc",
        "./NotoSansCJK-jp-Regular.otf",
    ]
    
    if system == "Windows":
        font_paths = [
            "C:/Windows/Fonts/msgothic.ttc",
            "C:/Windows/Fonts/msmincho.ttc",
            "C:/Windows/Fonts/NotoSansCJK-Regular.ttc",
        ]
    elif system == "Darwin":  # macOS
        font_paths = [
            "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
            "/Library/Fonts/NotoSansCJK-Regular.ttc",
            "/System/Library/Fonts/AppleGothic.ttf",
        ]
    else:  # Linux
        font_paths = [
            "/usr/share/fonts/truetype/takao-gothic/TakaoPGothic.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.otf",
        ]
    
    # ローカルフォントを最優先でチェック
    all_font_paths = local_font_paths + font_paths
    
    # フォントを試行
    for font_path in all_font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('Japanese', font_path))
                print(f"日本語フォントを登録しました: {font_path}")
                return 'Japanese'
            except Exception as e:
                print(f"フォント登録に失敗: {font_path} - {e}")
                continue
    
    # フォントが見つからない場合は英語のテスト文字を使用
    print("日本語フォントが見つかりません。英語のテスト文字を使用します。")
    print("日本語を使いたい場合は、以下のコマンドでフォントをダウンロードしてください：")
    print("mkdir -p fonts && wget -O fonts/NotoSansCJK-jp-Regular.otf https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansCJK-jp-Regular.otf")
    return None

def create_test_pdfs(output_dir="output"):
    """テスト用のPDFファイルを3種類作成（左回転、右回転、逆回転）"""
    
    # 出力ディレクトリを作成
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 日本語フォントのセットアップ
    japanese_font = setup_japanese_font()
    
    if japanese_font:
        test_text = "これは日本語のテストです\n正しい向きで読めますか？\n2024年8月7日"
    else:
        test_text = "This is a Japanese text test\nCan you read this correctly?\n2024-08-07"
    
    # 正常な向きのPDF
    normal_path = os.path.join(output_dir, "normal.pdf")
    c = canvas.Canvas(normal_path, pagesize=A4)
    width, height = A4
    
    # フォントを設定
    if japanese_font:
        c.setFont(japanese_font, 12)
    else:
        c.setFont("Helvetica", 12)
    
    y_pos = height - 100
    for line in test_text.split('\n'):
        c.drawString(100, y_pos, line)
        y_pos -= 30
    c.save()
    
    # 左回転（90度）のPDF作成
    doc = fitz.open(normal_path)
    page = doc[0]
    page.set_rotation(90)
    left_path = os.path.join(output_dir, "left_rotated.pdf")
    doc.save(left_path)
    doc.close()
    
    # 右回転（270度）のPDF作成
    doc = fitz.open(normal_path)
    page = doc[0]
    page.set_rotation(270)
    right_path = os.path.join(output_dir, "right_rotated.pdf")
    doc.save(right_path)
    doc.close()
    
    # 逆回転（180度）のPDF作成
    doc = fitz.open(normal_path)
    page = doc[0]
    page.set_rotation(180)
    upside_path = os.path.join(output_dir, "upside_down.pdf")
    doc.save(upside_path)
    doc.close()
    
    print(f"テスト用PDFを{output_dir}/に作成しました：")
    print(f"- {normal_path} (正常)")
    print(f"- {left_path} (左回転90度)")
    print(f"- {right_path} (右回転270度)")
    print(f"- {upside_path} (逆回転180度)")
    
    return [normal_path, left_path, right_path, upside_path]

def analyze_text_orientation_comparative(page, reference_positions=None):
    """基準位置と比較してテキストの向きを分析（比較ベース）"""
    
    print("🔍 比較ベースのテキスト配置分析を開始")
    
    # PDFメタデータの回転角度
    try:
        pdf_rotation = page.rotation
        print(f"📊 PDF回転メタデータ: {pdf_rotation}°")
    except Exception as e:
        print(f"❌ メタデータ取得エラー: {e}")
        pdf_rotation = 0
    
    # 現在のPDFのテキスト位置を取得
    current_positions = extract_text_positions(page)
    
    if not current_positions:
        print("⚠️ テキストが見つかりません。メタデータベースで判定")
        return get_rotation_from_metadata(pdf_rotation)
    
    # 基準位置が設定されている場合は比較分析
    if reference_positions:
        print("📊 基準位置との比較分析を実行")
        return compare_with_reference(current_positions, reference_positions)
    else:
        print("📊 絶対位置ベースの分析を実行")
        return analyze_absolute_position(current_positions)

def extract_text_positions(page):
    """ページからテキスト位置情報を抽出"""
    
    text_dict = page.get_text("dict")
    if not text_dict.get("blocks"):
        return []
    
    # ページサイズ情報
    page_rect = page.rect
    page_width = page_rect.width
    page_height = page_rect.height
    pdf_rotation = page.rotation
    
    # 元のページサイズを取得
    try:
        mediabox = page.mediabox
        original_width = mediabox.width
        original_height = mediabox.height
    except:
        original_width = page_width
        original_height = page_height
    
    text_positions = []
    
    for block in text_dict["blocks"]:
        if "lines" in block:
            for line in block["lines"]:
                for span in line["spans"]:
                    bbox = span["bbox"]
                    text = span["text"].strip()
                    
                    if text and len(text) > 2:
                        # 座標を元の座標系に変換
                        original_bbox = transform_coordinates_to_original(
                            bbox, page_width, page_height, pdf_rotation
                        )
                        
                        # 正規化座標（0-1の範囲）
                        normalized_x = (original_bbox[0] + original_bbox[2]) / 2 / original_width
                        normalized_y = (original_bbox[1] + original_bbox[3]) / 2 / original_height
                        
                        text_positions.append({
                            'text': text,
                            'normalized_x': normalized_x,
                            'normalized_y': normalized_y,
                            'original_bbox': original_bbox
                        })
    
    return text_positions

def compare_with_reference(current_positions, reference_positions):
    """基準位置と現在位置を比較して回転角度を決定"""
    
    if len(current_positions) == 0 or len(reference_positions) == 0:
        print("⚠️ 比較用のデータが不十分です")
        return 0
    
    print(f"📊 比較分析: 現在{len(current_positions)}個 vs 基準{len(reference_positions)}個")
    
    # 各回転角度での一致度を計算
    rotation_scores = {}
    
    for test_rotation in [0, 90, 180, 270]:
        # テスト回転を適用した位置を計算
        rotated_positions = apply_rotation_to_positions(current_positions, test_rotation)
        
        # 基準位置との一致度を計算
        score = calculate_position_similarity(rotated_positions, reference_positions)
        rotation_scores[test_rotation] = score
        
        print(f"   {test_rotation:3d}度回転での一致スコア: {score:.3f}")
    
    # 最も高いスコアの回転角度を選択
    best_rotation = max(rotation_scores, key=rotation_scores.get)
    best_score = rotation_scores[best_rotation]
    
    print(f"✅ 最適な回転角度: {best_rotation}度 (スコア: {best_score:.3f})")
    
    # 現在の回転から目標回転への差分を計算
    current_rotation = current_positions[0].get('current_rotation', 0) if current_positions else 0
    needed_rotation = (best_rotation - current_rotation) % 360
    
    # 360度を超える場合は負の値に変換
    if needed_rotation > 180:
        needed_rotation -= 360
    
    return needed_rotation

def apply_rotation_to_positions(positions, rotation_angle):
    """位置リストに回転を適用"""
    
    rotated_positions = []
    
    for pos in positions:
        x, y = pos['normalized_x'], pos['normalized_y']
        
        if rotation_angle == 0:
            new_x, new_y = x, y
        elif rotation_angle == 90:
            new_x, new_y = 1 - y, x
        elif rotation_angle == 180:
            new_x, new_y = 1 - x, 1 - y
        elif rotation_angle == 270:
            new_x, new_y = y, 1 - x
        else:
            new_x, new_y = x, y
        
        rotated_positions.append({
            'text': pos['text'],
            'normalized_x': new_x,
            'normalized_y': new_y
        })
    
    return rotated_positions

def calculate_position_similarity(positions1, positions2):
    """2つの位置リストの類似度を計算"""
    
    if len(positions1) == 0 or len(positions2) == 0:
        return 0.0
    
    total_similarity = 0.0
    compared_count = 0
    
    # 各テキストについて最も近い位置を探す
    for pos1 in positions1:
        best_distance = float('inf')
        
        for pos2 in positions2:
            # ユークリッド距離を計算
            distance = ((pos1['normalized_x'] - pos2['normalized_x']) ** 2 + 
                       (pos1['normalized_y'] - pos2['normalized_y']) ** 2) ** 0.5
            
            if distance < best_distance:
                best_distance = distance
        
        # 距離を類似度に変換（距離が小さいほど類似度が高い）
        similarity = max(0, 1 - best_distance * 2)  # 2は調整係数
        total_similarity += similarity
        compared_count += 1
    
    return total_similarity / compared_count if compared_count > 0 else 0.0

def analyze_absolute_position(positions):
    """絶対位置ベースで回転角度を決定（従来の方法）"""
    
    if not positions:
        return 0
    
    # テキストの平均位置を計算
    avg_x = sum(p['normalized_x'] for p in positions) / len(positions)
    avg_y = sum(p['normalized_y'] for p in positions) / len(positions)
    
    print(f"📍 正規化平均位置: ({avg_x:.2f}, {avg_y:.2f})")
    
    # 標準的な配置パターンで判定
    if avg_y < 0.4 and avg_x < 0.6:
        print("✅ 絶対位置判定: 正常（テキストが左上部）")
        return 0
    elif avg_y > 0.6 and avg_x > 0.4:
        print("✅ 絶対位置判定: 180度回転（テキストが右下部）")
        return 180
    elif avg_x < 0.4 and avg_y > 0.4:
        print("✅ 絶対位置判定: 90度左回転（テキストが左下部）")
        return -90
    elif avg_x > 0.6 and avg_y < 0.6:
        print("✅ 絶対位置判定: 90度右回転（テキストが右上部）")
        return 90
    else:
        print("🤔 絶対位置判定: 明確な判定困難")
        return 0

def choose_detection_method():
    """検出方法を選択するメニュー"""
    
    print("\n🔄 回転検出方法を選択してください:")
    print("1. 絶対位置ベース（基準ファイル不要、単体動作）")
    print("2. 相対位置ベース（基準ファイルとの比較、高精度）")
    print("3. 自動選択（基準ファイルがあれば相対、なければ絶対）")
    
    while True:
        try:
            choice = input("選択 (1/2/3): ").strip()
            if choice in ['1', '2', '3']:
                return int(choice)
            else:
                print("1、2、または3を入力してください。")
        except KeyboardInterrupt:
            print("\n処理を中断しました。")
            return 3  # デフォルト

def main():
    """メイン処理"""
    
    print("=== PDF回転検出・修正テスト ===\n")
    
    # 検出方法を選択
    method = choose_detection_method()
    
    # グローバル変数をリセット
    global _reference_positions, _detection_method
    _reference_positions = None
    _detection_method = method
    
    # ディレクトリの設定
    input_dir = "output"
    corrected_dir = "corrected"
    
    # correctedディレクトリをクリーンアップして再作成
    import shutil
    if os.path.exists(corrected_dir):
        shutil.rmtree(corrected_dir)
    
    os.makedirs(corrected_dir)
    
    print(f"\n1. 既存PDFファイルの確認")
    
    # 既存のPDFファイルをチェック（HTMLから生成されたもの）
    html_generated_files = []
    if os.path.exists(input_dir):
        for filename in os.listdir(input_dir):
            if filename.endswith('.pdf') and not filename.endswith('_real.pdf') and not filename.startswith('base'):
                html_generated_files.append(filename)
    
    if html_generated_files:
        print(f"✅ HTMLから生成されたPDFが見つかりました:")
        for pdf in sorted(html_generated_files):
            print(f"   - {pdf}")
        
        # HTMLから生成されたPDFから回転版を作成
        print(f"\n2. HTMLから生成されたPDFを使用して回転テストファイルを作成")
        base_file = os.path.join(input_dir, html_generated_files[0])
        
        if create_rotated_versions_from_html_pdf(base_file):
            test_files = ["normal.pdf", "left_rotated.pdf", "right_rotated.pdf", "upside_down.pdf"]
        else:
            print("❌ 回転版の作成に失敗しました")
            return
    else:
        # HTMLから生成されたファイルがない場合のみ、新規作成
        print("HTMLから生成されたPDFが見つかりません")
        print("2. 新規テスト用PDFを作成中...")
        
        if not create_test_pdfs_from_scratch():
            print("❌ テスト用PDFの作成に失敗しました")
            return
        
        test_files = ["normal.pdf", "left_rotated.pdf", "right_rotated.pdf", "upside_down.pdf"]
    
    # 選択された方法を表示
    method_names = {
        1: "絶対位置ベース",
        2: "相対位置ベース（基準ファイルとの比較）", 
        3: "自動選択"
    }
    print(f"\n📊 使用する検出方法: {method_names[method]}")
    
    print(f"\n3. 回転検出・修正を実行中...")
    
    for pdf_file in test_files:
        input_path = os.path.join(input_dir, pdf_file)
        
        if not os.path.exists(input_path):
            print(f"⚠️ ファイルが見つかりません: {input_path}")
            continue
            
        output_filename = pdf_file.replace('.pdf', '_corrected.pdf')
        output_path = os.path.join(corrected_dir, output_filename)
        
        print(f"\n処理中: {input_path}")
        try:
            detect_and_correct_rotation(input_path, output_path)
        except Exception as e:
            print(f"エラー: {e}")
    
    print("\n=== 処理完了 ===")
    print("ファイル構成：")
    print(f"{input_dir}/      - テスト用回転PDFファイル")
    print(f"{corrected_dir}/  - 回転修正済みファイル")
    print("\n🎯 修正済みファイルを確認してください。全て正しい向きになっているはずです。")

# グローバル変数で基準位置と検出方法を保存
_reference_positions = None
_detection_method = 3  # デフォルトは自動選択

def analyze_text_orientation(page):
    """テキストの向きを分析（選択された方法に基づく）"""
    
    global _reference_positions, _detection_method
    
    if _detection_method == 1:
        # 方法1: 絶対位置ベース
        print("🔍 絶対位置ベースの分析を実行")
        positions = extract_text_positions(page)
        return analyze_absolute_position(positions)
        
    elif _detection_method == 2:
        # 方法2: 相対位置ベース（強制）
        if _reference_positions is None:
            print("📌 基準位置を設定中...")
            _reference_positions = extract_text_positions(page)
            if _reference_positions:
                print(f"✅ 基準位置を記録: {len(_reference_positions)}個のテキスト要素")
                return 0  # 最初のファイルは正常と仮定
            else:
                print("⚠️ 基準位置の設定に失敗、絶対位置ベースにフォールバック")
                positions = extract_text_positions(page)
                return analyze_absolute_position(positions)
        else:
            return analyze_text_orientation_comparative(page, _reference_positions)
            
    else:
        # 方法3: 自動選択
        if _reference_positions is None:
            print("📌 基準位置を設定中...")
            _reference_positions = extract_text_positions(page)
            if _reference_positions:
                print(f"✅ 基準位置を記録: {len(_reference_positions)}個のテキスト要素")
                print("🔄 次のファイルからは相対位置ベースを使用します")
                return 0
            else:
                print("⚠️ 基準位置の設定に失敗、絶対位置ベースを使用")
                positions = extract_text_positions(page)
                return analyze_absolute_position(positions)
        else:
            return analyze_text_orientation_comparative(page, _reference_positions)

def transform_coordinates_to_original(bbox, page_width, page_height, rotation):
    """座標を回転前の元座標系に変換"""
    
    x0, y0, x1, y1 = bbox
    
    if rotation == 0:
        # 回転なし
        return [x0, y0, x1, y1]
    elif rotation == 90:
        # 90度回転 → 元に戻す変換
        return [y0, page_width - x1, y1, page_width - x0]
    elif rotation == 180:
        # 180度回転 → 元に戻す変換
        return [page_width - x1, page_height - y1, page_width - x0, page_height - y0]
    elif rotation == 270:
        # 270度回転 → 元に戻す変換
        return [page_height - y1, x0, page_height - y0, x1]
    else:
        # 不明な回転角度
        return [x0, y0, x1, y1]

def get_rotation_from_metadata(pdf_rotation):
    """PDFメタデータから回転角度を判定（従来の方法）"""
    
    if pdf_rotation == 90:
        return -90  # 90度回転 → -90度で修正
    elif pdf_rotation == 180:
        return 180  # 180度回転 → 180度で修正
    elif pdf_rotation == 270:
        return 90   # 270度回転 → 90度で修正
    else:
        return 0    # 修正不要

def detect_and_correct_rotation(input_pdf, output_pdf):
    """PDFの回転を検出して修正"""
    
    try:
        doc = fitz.open(input_pdf)
        corrected = False
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            print(f"\n--- ページ {page_num + 1} の分析 ---")
            try:
                current_rotation = page.rotation
                print(f"現在の回転角度: {current_rotation}")
                
                # テキストの向きを分析
                print("テキスト分析を開始...")
                suggested_rotation = analyze_text_orientation(page)
                
                print(f"推奨回転角度: {suggested_rotation}")
                
                if suggested_rotation != 0:
                    # 新しい回転角度を計算（現在の回転に追加）
                    new_rotation = (current_rotation + suggested_rotation) % 360
                    
                    print(f"回転を適用: {current_rotation}° + {suggested_rotation}° = {new_rotation}°")
                    
                    # 回転を適用
                    page.set_rotation(new_rotation)
                    corrected = True
                    
                    # 適用後の確認
                    try:
                        applied_rotation = page.rotation
                        print(f"適用後の回転角度: {applied_rotation}")
                    except:
                        print("適用後の回転角度確認をスキップ")
                else:
                    print("回転の必要なし")
                    
            except Exception as page_error:
                print(f"ページ {page_num + 1} の処理でエラー: {page_error}")
                import traceback
                traceback.print_exc()
                continue
        
        # ファイルを保存
        doc.save(output_pdf)
        doc.close()
        
        if corrected:
            print(f"\n修正済みPDFを保存: {output_pdf}")
        else:
            print(f"\n修正不要のため元ファイルをコピー: {output_pdf}")
        
        return corrected
        
    except Exception as e:
        print(f"PDF処理中にエラーが発生: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_rotated_versions_from_html_pdf(base_file_path):
    """HTMLから生成されたPDFを使って回転版を作成"""
    
    print(f"📄 ベースファイル: {base_file_path}")
    
    if not os.path.exists(base_file_path):
        print(f"❌ ベースファイルが見つかりません: {base_file_path}")
        return False
    
    try:
        output_dir = os.path.dirname(base_file_path)
        
        # まずベースファイルを別名でコピー
        temp_base = os.path.join(output_dir, "temp_base.pdf")
        import shutil
        shutil.copy2(base_file_path, temp_base)
        
        # 各回転パターンごとに処理
        rotation_configs = [
            (0, "normal.pdf", "正常版"),
            (90, "left_rotated.pdf", "左回転版"),
            (270, "right_rotated.pdf", "右回転版"),
            (180, "upside_down.pdf", "逆回転版")
        ]
        
        for rotation_angle, output_filename, description in rotation_configs:
            # テンポラリファイルから新しくドキュメントを開く
            doc = fitz.open(temp_base)
            page = doc[0]
            
            # 回転を適用
            page.set_rotation(rotation_angle)
            
            # 出力パス
            output_path = os.path.join(output_dir, output_filename)
            
            # 元ファイルと同じ名前の場合は一時的に別名で保存してから置き換え
            if os.path.abspath(output_path) == os.path.abspath(base_file_path):
                temp_output = os.path.join(output_dir, f"temp_{output_filename}")
                doc.save(temp_output)
                doc.close()
                
                # 元ファイルを削除してから置き換え
                os.remove(base_file_path)
                os.rename(temp_output, output_path)
            else:
                # 既存ファイルがある場合は削除
                if os.path.exists(output_path):
                    os.remove(output_path)
                
                doc.save(output_path)
                doc.close()
            
            print(f"✅ {description}: {output_filename} ({rotation_angle}度)")
        
        # テンポラリファイルを削除
        if os.path.exists(temp_base):
            os.remove(temp_base)
        
        print("✅ HTMLベースの日本語PDFから回転版を作成完了！")
        return True
        
    except Exception as e:
        print(f"❌ 回転版作成エラー: {e}")
        import traceback
        traceback.print_exc()
        return False
    """reportlabを使って最初からテスト用PDFを作成"""
    
    print("=== テスト用PDFを新規作成 ===")
    
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        
        # 出力ディレクトリを作成
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 日本語フォントの設定を試行
        font_name = "Helvetica"  # デフォルト
        japanese_available = False
        
        try:
            # システムの日本語フォントを試行
            import platform
            system = platform.system()
            
            if system == "Windows":
                font_paths = ["C:/Windows/Fonts/msgothic.ttc"]
            elif system == "Darwin":
                font_paths = ["/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"]
            else:
                font_paths = ["/usr/share/fonts/truetype/takao-gothic/TakaoPGothic.ttf"]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('Japanese', font_path))
                    font_name = "Japanese"
                    japanese_available = True
                    print(f"✅ 日本語フォント使用: {font_path}")
                    break
        except:
            pass
        
        # テスト用テキスト
        if japanese_available:
            test_text = [
                "これは日本語のテストです",
                "正しい向きで読めますか？",
                "2024年8月7日", 
                "PDF回転検出アルゴリズムのテスト用ページです"
            ]
        else:
            print("ℹ️ 日本語フォントが見つかりません。英語でテストします。")
            test_text = [
                "This is a PDF rotation test",
                "Can you read this text correctly?",
                "Date: August 7, 2025",
                "PDF Direction Corrector Test"
            ]
        
        # 正常なベースPDFを作成
        base_path = os.path.join(output_dir, "base.pdf")
        c = canvas.Canvas(base_path, pagesize=A4)
        width, height = A4
        
        # フォントを設定
        c.setFont(font_name, 14)
        
        # テキストを配置
        y_pos = height - 100
        for line in test_text:
            c.drawString(100, y_pos, line)
            y_pos -= 40
        c.save()
        
        print(f"✅ ベースPDF作成: {base_path}")
        
        # PyMuPDFでベースPDFから回転版を作成
        doc = fitz.open(base_path)
        page = doc[0]
        
        # 正常版 (0度)
        page.set_rotation(0)
        normal_path = os.path.join(output_dir, "normal.pdf")
        doc.save(normal_path)
        print(f"✅ 正常版: {normal_path} (0度)")
        
        # 左回転版 (90度)  
        page.set_rotation(90)
        left_path = os.path.join(output_dir, "left_rotated.pdf")
        doc.save(left_path)
        print(f"✅ 左回転版: {left_path} (90度)")
        
        # 右回転版 (270度)
        page.set_rotation(270)
        right_path = os.path.join(output_dir, "right_rotated.pdf")
        doc.save(right_path)
        print(f"✅ 右回転版: {right_path} (270度)")
        
        # 逆回転版 (180度)
        page.set_rotation(180)
        upside_path = os.path.join(output_dir, "upside_down.pdf")
        doc.save(upside_path)
        print(f"✅ 逆回転版: {upside_path} (180度)")
        
        doc.close()
        
        # ベースファイルを削除
        os.remove(base_path)
        
        language = "日本語" if japanese_available else "英語"
        print(f"\n{language}のテスト用PDFファイルが完成しました！")
        return True
        
    except ImportError:
        print("❌ reportlabがインストールされていません")
        print("uv add reportlab でインストールしてください")
        return False
    except Exception as e:
        print(f"PDF作成エラー: {e}")
        return False

def create_test_pdfs_from_scratch():
    """reportlabを使って最初からテスト用PDFを作成"""
    
    print("=== テスト用PDFを新規作成 ===")
    
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        
        # 出力ディレクトリを作成
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 日本語フォントの設定を試行
        font_name = "Helvetica"  # デフォルト
        japanese_available = False
        
        try:
            # システムの日本語フォントを試行
            import platform
            system = platform.system()
            
            if system == "Windows":
                font_paths = ["C:/Windows/Fonts/msgothic.ttc"]
            elif system == "Darwin":
                font_paths = ["/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"]
            else:
                font_paths = ["/usr/share/fonts/truetype/takao-gothic/TakaoPGothic.ttf"]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('Japanese', font_path))
                    font_name = "Japanese"
                    japanese_available = True
                    print(f"✅ 日本語フォント使用: {font_path}")
                    break
        except:
            pass
        
        # テスト用テキスト
        if japanese_available:
            test_text = [
                "これは日本語のテストです",
                "正しい向きで読めますか？",
                "2024年8月7日", 
                "PDF回転検出アルゴリズムのテスト用ページです"
            ]
        else:
            print("ℹ️ 日本語フォントが見つかりません。英語でテストします。")
            test_text = [
                "This is a PDF rotation test",
                "Can you read this text correctly?",
                "Date: August 7, 2025",
                "PDF Direction Corrector Test"
            ]
        
        # 正常なベースPDFを作成
        base_path = os.path.join(output_dir, "base.pdf")
        c = canvas.Canvas(base_path, pagesize=A4)
        width, height = A4
        
        # フォントを設定
        c.setFont(font_name, 14)
        
        # テキストを配置
        y_pos = height - 100
        for line in test_text:
            c.drawString(100, y_pos, line)
            y_pos -= 40
        c.save()
        
        print(f"✅ ベースPDF作成: {base_path}")
        
        # PyMuPDFでベースPDFから回転版を作成
        rotation_configs = [
            (0, "normal.pdf", "正常版"),
            (90, "left_rotated.pdf", "左回転版"),
            (270, "right_rotated.pdf", "右回転版"),
            (180, "upside_down.pdf", "逆回転版")
        ]
        
        for rotation_angle, output_filename, description in rotation_configs:
            doc = fitz.open(base_path)
            page = doc[0]
            
            page.set_rotation(rotation_angle)
            
            output_path = os.path.join(output_dir, output_filename)
            doc.save(output_path)
            doc.close()
            
            print(f"✅ {description}: {output_filename} ({rotation_angle}度)")
        
        # ベースファイルを削除
        os.remove(base_path)
        
        language = "日本語" if japanese_available else "英語"
        print(f"\n{language}のテスト用PDFファイルが完成しました！")
        return True
        
    except ImportError:
        print("❌ reportlabがインストールされていません")
        print("uv add reportlab でインストールしてください")
        return False
    except Exception as e:
        print(f"PDF作成エラー: {e}")
        return False

def main():
    """メイン処理"""
    
    print("=== PDF回転検出・修正テスト ===\n")
    
    # ディレクトリの設定
    input_dir = "output"
    corrected_dir = "corrected"
    
    # correctedディレクトリをクリーンアップして再作成
    import shutil
    if os.path.exists(corrected_dir):
        shutil.rmtree(corrected_dir)
    
    os.makedirs(corrected_dir)
    
    print("1. 既存PDFファイルの確認")
    
    # 既存のPDFファイルをチェック（HTMLから生成されたもの）
    html_generated_files = []
    if os.path.exists(input_dir):
        for filename in os.listdir(input_dir):
            if filename.endswith('.pdf') and not filename.endswith('_real.pdf') and not filename.startswith('base'):
                html_generated_files.append(filename)
    
    if html_generated_files:
        print(f"✅ HTMLから生成されたPDFが見つかりました:")
        for pdf in sorted(html_generated_files):
            print(f"   - {pdf}")
        
        # HTMLから生成されたPDFから回転版を作成
        print(f"\n2. HTMLから生成されたPDFを使用して回転テストファイルを作成")
        base_file = os.path.join(input_dir, html_generated_files[0])
        
        if create_rotated_versions_from_html_pdf(base_file):
            test_files = ["normal.pdf", "left_rotated.pdf", "right_rotated.pdf", "upside_down.pdf"]
        else:
            print("❌ 回転版の作成に失敗しました")
            return
    else:
        # HTMLから生成されたファイルがない場合のみ、新規作成
        print("HTMLから生成されたPDFが見つかりません")
        print("2. 新規テスト用PDFを作成中...")
        
        if not create_test_pdfs_from_scratch():
            print("❌ テスト用PDFの作成に失敗しました")
            return
        
        test_files = ["normal.pdf", "left_rotated.pdf", "right_rotated.pdf", "upside_down.pdf"]
    
    print(f"\n3. 回転検出・修正を実行中...")
    
    for pdf_file in test_files:
        input_path = os.path.join(input_dir, pdf_file)
        
        if not os.path.exists(input_path):
            print(f"⚠️ ファイルが見つかりません: {input_path}")
            continue
            
        output_filename = pdf_file.replace('.pdf', '_corrected.pdf')
        output_path = os.path.join(corrected_dir, output_filename)
        
        print(f"\n処理中: {input_path}")
        try:
            detect_and_correct_rotation(input_path, output_path)
        except Exception as e:
            print(f"エラー: {e}")
    
    print("\n=== 処理完了 ===")
    print("ファイル構成：")
    print(f"{input_dir}/      - テスト用回転PDFファイル")
    print(f"{corrected_dir}/  - 回転修正済みファイル")
    print("\n🎯 修正済みファイルを確認してください。全て正しい向きになっているはずです。")

def run():
    """エントリーポイント"""
    try:
        import fitz
        print(f"PyMuPDF バージョン: {fitz.version[0]}")
        main()
    except ImportError as e:
        print(f"必要なライブラリがインストールされていません: {e}")
        print("以下のコマンドでインストールしてください：")
        print("uv add PyMuPDF reportlab")

if __name__ == "__main__":
    run()