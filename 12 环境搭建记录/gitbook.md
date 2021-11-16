# gitbook和nginx关联

修改配置文件：

```
vim /usr/local/nginx/conf/nginx.conf
```

```
server {
        listen       4000;                		#nginx监听的端口
        server_name  117.51.142.225;         	#拦截的用户访问路径
        # 访问本地绝对路径下的静态html    
        location / {
            root   /root/EffectiveBlog/_book;	#gitbook build 生成的文件
            index  index.html index.htm;
		}
}
```

