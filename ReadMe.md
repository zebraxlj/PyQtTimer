* 设置环境
```sh
powershell.exe -ExecutionPolicy ByPass -NoExit -Command "& 'C:\ProgramData\miniconda3\shell\condabin\conda-hook.ps1' ; conda activate 'C:\ProgramData\miniconda3' "
conda create -n PyQt python=3.10
conda activate PyQt
python -m pip install --upgrade pip
pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
python -m pip install -r ./requirements.txt
```

* 运行环境
```sh
powershell.exe -ExecutionPolicy ByPass -NoExit -Command "& 'C:\ProgramData\miniconda3\shell\condabin\conda-hook.ps1' ; conda activate PyQt "
powershell.exe -ExecutionPolicy ByPass -NoExit -Command "& 'E:\ProgramFiles\anaconda3\shell\condabin\conda-hook.ps1' ; conda activate PyQt "
```

* 生成可执行文件
```sh
pyinstaller --clean --onefile --add-data "*.png;." --noconsole .\pomodoro.py
```