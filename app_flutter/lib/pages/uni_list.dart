import 'package:flutter/material.dart';

class UniListPage extends StatefulWidget {
  const UniListPage({super.key});

  @override
  State<UniListPage> createState() => _UniListPageState();
}

class _UniListPageState extends State<UniListPage> {
  final List<Map<String, String>> _items = [];
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _loading = true);
    // TODO: 加载数据
    await Future.delayed(const Duration(seconds: 1));
    if (!mounted) return;
    setState(() {
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('UniList')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _items.isEmpty
              ? const Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.inbox_outlined, size: 64, color: Colors.grey),
                      SizedBox(height: 16),
                      Text('暂无数据', style: TextStyle(color: Colors.grey)),
                    ],
                  ),
                )
              : ListView.builder(
                  itemCount: _items.length,
                  itemBuilder: (context, index) {
                    final item = _items[index];
                    return ListTile(
                      title: Text(item['title'] ?? ''),
                      subtitle: Text(item['subtitle'] ?? ''),
                    );
                  },
                ),
    );
  }
}
