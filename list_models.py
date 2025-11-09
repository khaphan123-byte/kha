import google.generativeai as genai

# Cấu hình API key
genai.configure(api_key="AIzaSyD2Cu-EcUfJUUmHfvYtl1oPEvUIvg-u2SQ")  # thay bằng key thật

# Lấy danh sách model
models = genai.list_models()
for m in models:
    print(f"{m.name} — supports: {m.supported_generation_methods}")
