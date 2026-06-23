import 'dart:convert';
import 'package:http/http.dart' as http;

class AIService {
  // 在 Termux 局域网或者真机调试时，127.0.0.1 适用。
  static const String _baseUrl = 'http://127.0.0.1:8000';

  static Future<List<dynamic>> recommend({
    required String score,
    String province = '湖北省',
  }) async {
    final response = await http.post(
      Uri.parse('$_baseUrl/api/v1/recommend'), // 对应后端的路由
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'score': int.tryParse(score) ?? 0,
        'province': province,
        'subject_type': '物理', // 补齐后端定义的字段
      }),
    );

    if (response.statusCode != 200) {
      throw Exception('服务器错误: ${response.statusCode}');
    }

    final data = jsonDecode(response.body);
    
    // 后端返回的格式是 { "status": "success", "data": [...] }
    if (data['status'] == 'success') {
      return data['data'] as List<dynamic>;
    } else {
      throw Exception('推荐失败：状态异常');
    }
  }
}
