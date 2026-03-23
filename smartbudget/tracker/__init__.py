import os

if os.getenv('MYSQL_DATABASE'):
	import pymysql

	pymysql.install_as_MySQLdb()
