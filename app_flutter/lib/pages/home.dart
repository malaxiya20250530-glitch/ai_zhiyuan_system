import 'package:flutter/material.dart';
import '../api/ai_service.dart';
import 'result.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final _formKey = GlobalKey<FormState>();
  final TextEditingController _scoreController = TextEditingController();
  final TextEditingController _provinceController = TextEditingController(
    text: '湖北省',
  );

  String _selectedSubject = '物理';
  bool _loading = false;

  static const List<String> _subjects = ['物理', '历史'];

  @override
  void dispose() {
    _scoreController.dispose();
    _provinceController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _loading = true);

    try {
      final response = await AIService.recommend(
        score: _scoreController.text.trim(),
        province: _provinceController.text.trim(),
        subjectType: _selectedSubject,
      );

      if (!mounted) return;

      if (response.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('暂无推荐结果，请稍后再试')),
        );
        return;
      }

      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => ResultPage(
            items: response.items,
            score: _scoreController.text.trim(),
            meta: response.meta,
          ),
        ),
      );
    } on AIServiceException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(e.message),
          backgroundColor: Colors.red.shade700,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('未知错误: $e'),
          backgroundColor: Colors.red.shade700,
        ),
      );
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('AI 志愿推荐'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline),
            onPressed: () => _showAboutDialog(context),
          ),
        ],
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 32),
          child: Form(
            key: _formKey,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // ── 头部图标 ──
                Icon(Icons.school_rounded, size: 88, color: theme.colorScheme.primary),
                const SizedBox(height: 12),
                Text(
                  '高考志愿智能推荐',
                  style: theme.textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  '基于双流觉察推理，推荐最适合你的院校',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
                const SizedBox(height: 36),

                // ── 省份输入 ──
                TextFormField(
                  controller: _provinceController,
                  decoration: const InputDecoration(
                    labelText: '省份',
                    hintText: '例如：湖北省',
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.location_on_outlined),
                  ),
                  validator: (v) =>
                      (v == null || v.trim().isEmpty) ? '请输入省份' : null,
                ),
                const SizedBox(height: 16),

                // ── 选科选择 ──
                DropdownButtonFormField<String>(
                  value: _selectedSubject,
                  decoration: const InputDecoration(
                    labelText: '选科类别',
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.category_outlined),
                  ),
                  items: _subjects.map((s) {
                    return DropdownMenuItem(value: s, child: Text(s));
                  }).toList(),
                  onChanged: (v) {
                    if (v != null) setState(() => _selectedSubject = v);
                  },
                ),
                const SizedBox(height: 16),

                // ── 分数输入 ──
                TextFormField(
                  controller: _scoreController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: '高考分数',
                    hintText: '例如：600',
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.score_outlined),
                  ),
                  validator: (v) {
                    if (v == null || v.trim().isEmpty) return '请输入分数';
                    final n = int.tryParse(v.trim());
                    if (n == null || n < 0 || n > 750) return '请输入有效分数（0-750）';
                    return null;
                  },
                ),
                const SizedBox(height: 32),

                // ── 提交按钮 ──
                SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: FilledButton.icon(
                    onPressed: _loading ? null : _submit,
                    icon: _loading
                        ? const SizedBox(
                            width: 22,
                            height: 22,
                            child: CircularProgressIndicator(
                              strokeWidth: 2.5,
                              color: Colors.white,
                            ),
                          )
                        : const Icon(Icons.auto_awesome),
                    label: Text(
                      _loading ? 'AI 推理中…' : '开始智能推荐',
                      style: const TextStyle(fontSize: 17),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _showAboutDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.psychology, color: Colors.blue),
            SizedBox(width: 8),
            Text('双流觉察推理'),
          ],
        ),
        content: const Text(
          '系统采用「双流觉察推理 (Dual-Stream Aware Reasoning)」技术：\n\n'
          '① 刚性觉察 — 对照投档线数据，筛选冲/稳/保梯度院校\n'
          '② 柔性觉察 — 匹配学科属性与就业韧性，推荐最适专业',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('知道了'),
          ),
        ],
      ),
    );
  }
}
