import os
import json
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# --- 配置 ---
# 请将此路径设置为您的结果文件所在的根目录
# BASE_DIR = '/users/muhan/faasnap/results/expr-batch-2025-08-11T21-06-59'
# BASE_DIR = '/users/muhan/faasnap/results/expr-batch-2025-08-11T08-51-53'
# BASE_DIR = '/users/muhan/faasnap/results/expr-batch-2025-08-12T04-12-13'
BASE_DIR='/users/muhan/faasnap/results/expr-batch-2025-08-12T05-04-31'

# 假设JSON文件中延迟的键是 'latency'。
LATENCY_KEY = 'latency'


def collect_latency_data(base_path):
    """
    步骤 1: 遍历指定的目录结构，收集原始的、逐次运行的延迟数据。
    """
    # (此函数保持不变)
    all_data = []
    print(f"步骤 1: 开始在目录 '{os.path.abspath(base_path)}' 中收集原始数据...")
    if not os.path.isdir(base_path):
        print(f"错误: 目录 '{base_path}' 不存在。请检查 BASE_DIR 配置。")
        return []
    dir_list = os.listdir(base_path)
    if not dir_list:
        print("警告: 目标目录为空，找不到任何实验数据。")
        return []
    for dir_name in dir_list:
        full_dir_path = os.path.join(base_path, dir_name)
        if os.path.isdir(full_dir_path) and '_' in dir_name:
            parts = dir_name.split('_');
            if len(parts) < 2: continue
            setting_string = parts[0];
            setting_parts = setting_string.split('-')
            if len(setting_parts) < 2: continue
            storage_type = setting_parts[-1];
            framework_name = '-'.join(setting_parts[:-1])
            function_name = parts[1]
            try:
                round_dirs = sorted([d for d in os.listdir(full_dir_path) if os.path.isdir(os.path.join(full_dir_path, d))], key=int)
            except (ValueError, TypeError):
                continue
            for round_num_str in round_dirs:
                round_path = os.path.join(full_dir_path, round_num_str)
                for filename in os.listdir(round_path):
                    if filename.endswith('.json'):
                        json_path = os.path.join(round_path, filename)
                        try:
                            with open(json_path, 'r') as f:
                                data = json.load(f);
                                latency = data.get(LATENCY_KEY)
                                if latency is not None:
                                    all_data.append({'framework': framework_name, 'storage': storage_type, 'function': function_name, 'round': int(round_num_str), 'latency': float(latency)})
                                else:
                                    print(f"  - 警告: 在文件 '{json_path}' 中未找到键 '{LATENCY_KEY}'。")
                                break
                        except Exception as e:
                            print(f"  - 错误: 读取或解析文件 '{json_path}' 时出错: {e}")
    print("步骤 1: 原始数据收集完成。")
    return all_data


def process_and_summarize_data(df):
    """
    步骤 2: 处理收集到的数据，计算每个实验组合的平均值和其他统计数据。
    """
    # (此函数保持不变)
    print("\n步骤 2: 开始处理数据并计算统计摘要...")
    if df.empty: print("警告: 没有数据可供处理。"); return None
    aggregations = {'latency': ['mean', 'std', 'median', 'min', 'max']}
    summary_df = df.groupby(['framework', 'storage', 'function']).agg(aggregations)
    summary_df.columns = ['_'.join(col).strip() for col in summary_df.columns.values]
    summary_df = summary_df.reset_index()
    summary_df['stability_cv'] = (summary_df['latency_std'] / summary_df['latency_mean']).fillna(0)
    summary_df = summary_df.rename(columns={'latency_mean': 'mean_latency', 'latency_std': 'std_dev_latency', 'latency_median': 'median_latency', 'latency_min': 'min_latency', 'latency_max': 'max_latency'})
    print("步骤 2: 数据处理和汇总完成。")
    return summary_df


def plot_latency_distribution(df, output_prefix):
    """
    步骤 3: 可视化延迟分布，并保存为图像文件。
    """
    # (此函数保持不变)
    print("\n步骤 3: 开始生成延迟分布图...")
    if df.empty: print("警告: 没有数据可供绘图。"); return
    sns.set_theme(style="whitegrid")
    global_function_order = df.groupby('function')['latency'].median().sort_values().index
    framework_order = sorted(df['framework'].unique())
    colors = sns.color_palette("colorblind", n_colors=len(framework_order)); color_palette = dict(zip(framework_order, colors))
    storage_types = df['storage'].unique()
    for storage_type in storage_types:
        fig, ax = plt.subplots(figsize=(20, 10))
        storage_df = df[df['storage'] == storage_type].copy()
        print(f"    - 正在为 '{storage_type}' 存储生成分布图...")
        sns.boxplot(data=storage_df, x='function', y='latency', hue='framework', order=global_function_order, hue_order=framework_order, palette=color_palette, ax=ax, showfliers=False)
        sns.stripplot(data=storage_df, x='function', y='latency', hue='framework', order=global_function_order, hue_order=framework_order, dodge=True, ax=ax, alpha=0.6, s=5, palette=['#404040']*len(framework_order))
        ax.set_yscale('log'); ax.set_title(f'Latency Distribution on "{storage_type.upper()}" Storage (Log Scale)', fontsize=22, pad=20)
        ax.set_xlabel('Function', fontsize=16); ax.set_ylabel('Latency (seconds) - Log Scale', fontsize=16)
        plt.xticks(rotation=45, ha='right', fontsize=12); plt.yticks(fontsize=12)
        handles, labels = ax.get_legend_handles_labels(); ax.legend(handles[:len(framework_order)], labels[:len(framework_order)], title='Framework', fontsize=14)
        plt.tight_layout()
        plot_filename = f'{output_prefix}-latency_distribution_{storage_type}.png'
        plt.savefig(plot_filename, dpi=300)
        print(f"    ✅ 分布图已保存到 '{plot_filename}'")


# --- 新增的对比图功能 ---
def plot_storage_comparison(summary_df, output_prefix):
    """
    步骤 4: 创建哑铃图，对比 'local' 和 'nfs' 存储的性能差异。
    """
    print("\n步骤 4: 开始生成存储性能对比图 (哑铃图)...")
    if summary_df.empty:
        print("警告: 没有汇总数据可供绘图。")
        return

    # 1. 重塑数据，将 local 和 nfs 的延迟放到同一行
    try:
        pivoted_df = summary_df.pivot_table(
            index=['framework', 'function'],
            columns='storage',
            values='mean_latency'
        ).reset_index()
        pivoted_df = pivoted_df.dropna(subset=['local', 'nfs']) # 只保留同时有local和nfs数据的项
    except KeyError:
        print("错误: 数据中必须同时包含 'local' 和 'nfs' 的结果才能生成对比图。")
        return

    if pivoted_df.empty:
        print("警告: 没有找到可以同时用于 'local' 和 'nfs' 对比的数据。")
        return

    # 2. 准备绘图
    frameworks = pivoted_df['framework'].unique()
    fig, axes = plt.subplots(nrows=len(frameworks), ncols=1, figsize=(12, 6 * len(frameworks)), sharex=True)
    fig.suptitle('Latency Comparison: Local vs. NFS Storage\n(Lower is Better)', fontsize=20)

    # 定义颜色
    colors = {"local": "#0072B2", "nfs": "#D55E00"} # 蓝色和橙色

    # 3. 为每个框架创建一个子图
    for i, framework in enumerate(frameworks):
        ax = axes[i]
        framework_data = pivoted_df[pivoted_df['framework'] == framework].copy()
        # 按 NFS 延迟排序，以便观察
        framework_data = framework_data.sort_values('nfs', ascending=False)
        
        # 创建 y 轴的位置
        y_range = np.arange(len(framework_data))
        
        # 绘制水平线 (哑铃的“柄”)
        ax.hlines(y=y_range, xmin=framework_data['local'], xmax=framework_data['nfs'], 
                  color='grey', alpha=0.5, zorder=1)
        
        # 绘制圆点 (哑铃的“头”)
        ax.scatter(framework_data['local'], y_range, color=colors['local'], s=60, label='Local', zorder=2)
        ax.scatter(framework_data['nfs'], y_range, color=colors['nfs'], s=60, label='NFS', zorder=2)
        
        # 4. 美化子图
        ax.set_xscale('log')
        ax.set_yticks(y_range)
        ax.set_yticklabels(framework_data['function'], fontsize=12)
        ax.set_title(f'Framework: {framework}', fontsize=16, loc='left')
        ax.grid(axis='x', linestyle='--', alpha=0.7)
        ax.invert_yaxis() # 让延迟最高的函数显示在最上方

    # 5. 美化整个图表
    # 创建统一的图例
    handles = [plt.Line2D([0], [0], marker='o', color='w', label='Local', markersize=10, markerfacecolor=colors['local']),
               plt.Line2D([0], [0], marker='o', color='w', label='NFS', markersize=10, markerfacecolor=colors['nfs'])]
    fig.legend(handles=handles, loc='upper right', fontsize=14, bbox_to_anchor=(0.95, 0.98))
    
    plt.xlabel('Mean Latency (seconds) - Log Scale', fontsize=14)
    plt.tight_layout(rect=[0, 0, 1, 0.96]) # 调整布局为总标题留出空间

    # 保存图表
    plot_filename = f'{output_prefix}-storage_comparison_dumbbell_plot.png'
    plt.savefig(plot_filename, dpi=300)
    print(f"    ✅ 存储对比图已保存到 '{plot_filename}'")


if __name__ == "__main__":
    output_prefix = os.path.join(os.path.dirname(BASE_DIR), os.path.basename(BASE_DIR))

    # --- 阶段 1: 收集 ---
    raw_data = collect_latency_data(BASE_DIR)

    if raw_data:
        df_detailed = pd.DataFrame(raw_data)
        detailed_csv_file = f'{output_prefix}-latencies_detailed.csv'
        df_detailed.to_csv(detailed_csv_file, index=False)
        print(f"\n✅ 原始详细数据已保存到 '{detailed_csv_file}'")

        # --- 阶段 2: 汇总 ---
        df_summary = process_and_summarize_data(df_detailed)
        if df_summary is not None:
            summary_csv_file = f'{output_prefix}-latency_summary.csv'
            df_summary.to_csv(summary_csv_file, index=False, float_format='%.6f')
            print(f"✅ 汇总分析结果已保存到 '{summary_csv_file}'")
            print("\n" + "="*80); print("汇总结果预览:"); print(df_summary[['framework', 'storage', 'function', 'mean_latency', 'stability_cv']]); print("="*80)

        # --- 阶段 3: 绘制分布图 ---
        plot_latency_distribution(df_detailed, output_prefix)

        # --- 阶段 4: 绘制存储对比图 ---
        if df_summary is not None:
            plot_storage_comparison(df_summary, output_prefix)

    else:
        print("\n未能收集到任何数据，请检查您的目录结构和 BASE_DIR 配置是否正确。")