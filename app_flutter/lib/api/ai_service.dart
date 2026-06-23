import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

/// AI 志愿推荐系统 — 网络请求层
///
/// 连接后端「双流觉察推理」API。
/// 在同一台手机上调试时，127.0.0.1 可用；
/// 若 Flutter App 在另一台设备运行，请改为后端所在设备的局域网 IP。
class AIService {
  // ─── 可配置基址 ───────────────────────────────────────────────
  // 自动检测：Android 模拟器用 10.0.2.2，真机用 127.0.0.1
  static String get _defaultHost {
    if (Platform.isAndroid) {
      // Android 真机：后端跑在同一个 Termux 里，用 localhost
      return '127.0.0.1';
    }
    return '127.0.0.1';
  }

  static const int _defaultPort = 8000;

  /// 如需改为局域网 IP，直接修改此变量即可：
  ///   AIService.baseUrl = 'http://192.168.1.100:8000';
  static String baseUrl = 'http://$_defaultHost:$_defaultPort';

  static const Duration _timeout = Duration(seconds: 15);

  // ─── 请求参数 ─────────────────────────────────────────────────
  static const Map<String, String> _headers = {
    'Content-Type': 'application/json',
  };

  /// 获取推荐结果（双流觉察推理）
  ///
  /// [score]      高考分数
  /// [province]   省份，默认湖北省
  /// [subjectType] 选科，默认物理
  static Future<RecommendResponse> recommend({
    required String score,
    String province = '湖北省',
    String subjectType = '物理',
    String? rank,
  }) async {
    final uri = Uri.parse('$baseUrl/api/v1/recommend');

    final body = jsonEncode({
      'score': int.tryParse(score) ?? 0,
      'province': province,
      'subject_type': subjectType,
      if (rank != null && rank.isNotEmpty) 'rank': int.tryParse(rank),
    });

    http.Response response;
    try {
      response = await http
          .post(uri, headers: _headers, body: body)
          .timeout(_timeout);
    } on SocketException {
      throw AIServiceException('无法连接到服务器（$baseUrl），请检查后端是否启动');
    } on http.ClientException {
      throw AIServiceException('网络请求失败，请检查网络连接');
    } catch (e) {
      if (e is AIServiceException) rethrow;
      throw AIServiceException('请求超时或网络异常');
    }

    if (response.statusCode != 200) {
      throw AIServiceException(
        '服务器返回错误 (${response.statusCode})',
      );
    }

    final Map<String, dynamic> decoded;
    try {
      decoded = jsonDecode(response.body) as Map<String, dynamic>;
    } catch (_) {
      throw AIServiceException('服务器返回格式异常，无法解析');
    }

    if (decoded['status'] != 'success') {
      throw AIServiceException('推荐失败：${decoded['message'] ?? '状态异常'}');
    }

    final rawData = decoded['data'];
    if (rawData == null || rawData is! List) {
      throw AIServiceException('推荐结果为空，请稍后再试');
    }

    // 解析成类型安全的数据模型
    final items = rawData
        .map((e) => RecommendItem.fromJson(e as Map<String, dynamic>))
        .toList();

    return RecommendResponse(
      items: items,
      meta: decoded['meta'] as Map<String, dynamic>?,
    );
  }
}

// ─── 数据模型 ──────────────────────────────────────────────────

class RecommendItem {
  final String university;
  final String major;
  final String probability; // "冲刺" / "稳妥" / "保底"
  final int? minRank;

  const RecommendItem({
    required this.university,
    required this.major,
    required this.probability,
    this.minRank,
  });

  factory RecommendItem.fromJson(Map<String, dynamic> json) {
    return RecommendItem(
      university: json['university'] as String? ?? '未知院校',
      major: json['major'] as String? ?? '未指定专业',
      probability: json['probability'] as String? ?? '未知',
      minRank: json['min_rank'] as int?,
    );
  }
}

class RecommendResponse {
  final List<RecommendItem> items;
  final Map<String, dynamic>? meta;

  const RecommendResponse({required this.items, this.meta});

  bool get isEmpty => items.isEmpty;
  int get length => items.length;
}

class AIServiceException implements Exception {
  final String message;
  const AIServiceException(this.message);

  @override
  String toString() => message;
}
