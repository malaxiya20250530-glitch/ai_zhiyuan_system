import 'package:flutter/material.dart';
import '../api/ai_service.dart';

class ResultPage extends StatelessWidget {
  final List<RecommendItem> items;
  final String score;
  final Map<String, dynamic>? meta;

  const ResultPage({
    super.key,
    required this.items,
    required this.score,
    this.meta,
  });

  // ── 概率等级 → 颜色映射 ──
  static Color _colorFor(String probability) {
    switch (probability) {
      case '冲刺':
        return Colors.redAccent;
      case '稳妥':
        return Colors.orange;
      case '保底':
        return Colors.green;
      default:
        return Colors.blueGrey;
    }
  }

  // ── 概率等级 → 图标映射 ──
  static IconData _iconFor(String probability) {
    switch (probability) {
      case '冲刺':
        return Icons.trending_up;
      case '稳妥':
        return Icons.check_circle_outline;
      case '保底':
        return Icons.verified_outlined;
      default:
        return Icons.help_outline;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    // ── 分组排序：冲刺 → 稳妥 → 保底 ──
    final order = {'冲刺': 0, '稳妥': 1, '保底': 2, '未知': 3};
    final sorted = List<RecommendItem>.from(items)
      ..sort((a, b) => (order[a.probability] ?? 3).compareTo(order[b.probability] ?? 3));

    return Scaffold(
      appBar: AppBar(
        title: Text('推荐结果 ($score 分)'),
        centerTitle: true,
        elevation: 1,
      ),
      body: sorted.isEmpty
          ? const Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.inbox_outlined, size: 64, color: Colors.grey),
                  SizedBox(height: 16),
                  Text('暂无推荐结果', style: TextStyle(fontSize: 18, color: Colors.grey)),
                ],
              ),
            )
          : Column(
              children: [
                // ── 统计摘要 ──
                _SummaryBar(items: sorted),
                // ── 推荐列表 ──
                Expanded(
                  child: ListView.builder(
                    padding: const EdgeInsets.fromLTRB(12, 4, 12, 24),
                    itemCount: sorted.length,
                    itemBuilder: (context, i) => _ResultCard(
                      item: sorted[i],
                      index: i + 1,
                    ),
                  ),
                ),
              ],
            ),
    );
  }
}

// ─── 顶部统计摘要 ─────────────────────────────────────────────

class _SummaryBar extends StatelessWidget {
  final List<RecommendItem> items;
  const _SummaryBar({required this.items});

  @override
  Widget build(BuildContext context) {
    final counts = <String, int>{};
    for (final item in items) {
      counts[item.probability] = (counts[item.probability] ?? 0) + 1;
    }

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
      color: Theme.of(context).colorScheme.surfaceContainerLow,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _BadgeStat(label: '冲刺', count: counts['冲刺'] ?? 0, color: Colors.redAccent),
          _BadgeStat(label: '稳妥', count: counts['稳妥'] ?? 0, color: Colors.orange),
          _BadgeStat(label: '保底', count: counts['保底'] ?? 0, color: Colors.green),
        ],
      ),
    );
  }
}

class _BadgeStat extends StatelessWidget {
  final String label;
  final int count;
  final Color color;
  const _BadgeStat({required this.label, required this.count, required this.color});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
          decoration: BoxDecoration(
            color: color.withAlpha(25),
            borderRadius: BorderRadius.circular(4),
            border: Border.all(color: color.withAlpha(80)),
          ),
          child: Text(label, style: TextStyle(fontSize: 13, color: color, fontWeight: FontWeight.w600)),
        ),
        const SizedBox(width: 6),
        Text('$count', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: color)),
      ],
    );
  }
}

// ─── 单条推荐卡片 ─────────────────────────────────────────────

class _ResultCard extends StatelessWidget {
  final RecommendItem item;
  final int index;
  const _ResultCard({required this.item, required this.index});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final badgeColor = ResultPage._colorFor(item.probability);
    final badgeIcon = ResultPage._iconFor(item.probability);

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 6),
      elevation: 1.5,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── 序号 ──
            CircleAvatar(
              radius: 16,
              backgroundColor: badgeColor.withAlpha(30),
              child: Text(
                '$index',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  color: badgeColor,
                ),
              ),
            ),
            const SizedBox(width: 14),

            // ── 院校 & 专业 ──
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    item.university,
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Row(
                    children: [
                      Icon(Icons.book_outlined, size: 16, color: theme.colorScheme.onSurfaceVariant),
                      const SizedBox(width: 4),
                      Text(
                        item.major,
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: theme.colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                  if (item.minRank != null) ...[
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Icon(Icons.format_list_numbered, size: 14, color: theme.colorScheme.onSurfaceVariant),
                        const SizedBox(width: 4),
                        Text(
                          '参考位次: ${item.minRank}',
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: theme.colorScheme.outline,
                          ),
                        ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(width: 8),

            // ── 概率标签 ──
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: badgeColor.withAlpha(25),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: badgeColor.withAlpha(100)),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(badgeIcon, size: 16, color: badgeColor),
                  const SizedBox(width: 4),
                  Text(
                    item.probability,
                    style: TextStyle(
                      color: badgeColor,
                      fontWeight: FontWeight.bold,
                      fontSize: 15,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
