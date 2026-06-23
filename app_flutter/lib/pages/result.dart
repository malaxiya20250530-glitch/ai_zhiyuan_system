import 'package:flutter/material.dart';

class ResultPage extends StatelessWidget {
  final List<dynamic> data;
  final String score;

  const ResultPage({
    super.key,
    required this.data,
    required this.score,
  });

  // 根据 AI 返回的文字状态（冲刺/稳妥/保底）匹配不同的颜色
  Color _getProbabilityColor(String? probability) {
    switch (probability) {
      case '冲刺':
        return Colors.redAccent;
      case '稳妥':
        return Colors.orange;
      case '保底':
        return Colors.green;
      default:
        return Colors.blue;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('AI 智能推荐结果 ($score分)'),
        elevation: 2,
      ),
      body: data.isEmpty
          ? const Center(child: Text('暂无 AI 推荐结果，请稍后再试'))
          : ListView.builder(
              padding: const EdgeInsets.all(12),
              itemCount: data.length,
              itemBuilder: (context, i) {
                final item = data[i];
                final university = item['university'] as String? ?? '未知大学';
                final major = item['major'] as String? ?? '未指定专业';
                final probability = item['probability'] as String? ?? '未知';
                final minRank = item['min_rank'];

                final badgeColor = _getProbabilityColor(probability);

                return Card(
                  margin: const EdgeInsets.symmetric(vertical: 8),
                  elevation: 2,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // 左侧院校及专业信息
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                university,
                                style: const TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              const SizedBox(height: 8),
                              Row(
                                children: [
                                  const Icon(Icons.book, size: 16, color: Colors.grey),
                                  const SizedBox(width: 4),
                                  Expanded(
                                    child: Text(
                                      '推荐专业: $major',
                                      style: TextStyle(
                                        fontSize: 14,
                                        color: Colors.grey[700],
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                              if (minRank != null) ...[
                                const SizedBox(height: 4),
                                Text(
                                  '建议参考位次: $minRank',
                                  style: const TextStyle(
                                    fontSize: 12,
                                    color: Colors.grey,
                                  ),
                                ),
                              ],
                            ],
                          ),
                        ),
                        const SizedBox(width: 12),
                        // 右侧录取概率标签
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 6,
                          ),
                          decoration: BoxDecoration(
                            color: badgeColor.withAlpha(30),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: badgeColor, width: 1),
                          ),
                          child: Text(
                            probability,
                            style: TextStyle(
                              color: badgeColor,
                              fontWeight: FontWeight.bold,
                              fontSize: 14,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
    );
  }
}
