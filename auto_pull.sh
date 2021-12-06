#一但有任何一个语句返回非真的值，则退出
set -e

cd /root/EffectiveBlog/

git pull

gitbook build