import errno
import shutil
import os


def get_desktop_path():
    """适用于标准英文系统（不推荐用于多语言环境）"""
    return os.path.join(os.path.expanduser("~"), "Desktop")


def copy_to_desktop(source_path, overwrite=False, preserve_metadata=True):
    """
    将指定文件复制到桌面
    
    参数:
    source_path (str): 源文件的完整路径
    overwrite (bool): 如果目标文件存在，是否覆盖 (默认 False)
    preserve_metadata (bool): 是否保留文件元数据 (默认 True)
    
    返回:
    str: 桌面上新文件的完整路径
    
    异常:
    FileNotFoundError: 源文件不存在
    PermissionError: 没有权限访问文件或桌面
    OSError: 复制过程中发生其他错误
    """
    # 验证源文件是否存在
    if not os.path.exists(source_path):
        raise FileNotFoundError(errno.ENOENT, f"源文件不存在: {source_path}")
    
    # 获取桌面路径
    try:
        desktop_path = get_desktop_path()
    except Exception as e:
        raise OSError(f"无法获取桌面路径: {str(e)}") from e
    
    # 确保桌面路径存在
    if not os.path.exists(desktop_path):
        os.makedirs(desktop_path, exist_ok=True)
    
    # 构建目标路径
    filename = os.path.basename(source_path)
    dest_path = os.path.join(desktop_path, filename)
    
    # 检查目标文件是否存在
    if os.path.exists(dest_path):
        if overwrite:
            # 删除现有文件
            try:
                os.remove(dest_path)
            except PermissionError:
                raise PermissionError(f"没有权限覆盖桌面文件: {dest_path}")
        else:
            # 生成唯一文件名 (添加序号)
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(dest_path):
                dest_path = os.path.join(desktop_path, f"{base} ({counter}){ext}")
                counter += 1
    
    # 执行复制操作
    try:
        if preserve_metadata:
            # 复制文件并保留元数据 (创建时间、修改时间等)
            shutil.copy2(source_path, dest_path)
        else:
            # 仅复制文件内容
            shutil.copyfile(source_path, dest_path)
    except PermissionError:
        raise PermissionError(f"没有权限写入桌面: {dest_path}")
    except Exception as e:
        raise OSError(f"复制文件时出错: {str(e)}") from e
    
    return dest_path

def createOrange():
    try:
        source_file = r"E:\myDemo\tes\orange.ico"
        new_path = copy_to_desktop(source_file, overwrite=False)
        print(f"文件已成功复制到桌面:\n{new_path}")
        
        # 示例：复制另一个文件（不覆盖同名文件）
        # new_path = copy_to_desktop(r"C:\path\to\your\file.txt", overwrite=False)
        # print(f"文件已复制到桌面 (保留原文件):\n{new_path}")
        
    except Exception as e:
        print(f"操作失败: {str(e)}")


# 使用示例
if __name__ == "__main__":
    createOrange()