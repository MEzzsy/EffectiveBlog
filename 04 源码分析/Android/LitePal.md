# LitePal

LitePal是郭神写的一个数据存储库，功能强大，准备看看源码学习一下。

## 基本使用

**导入依赖**

```
compile 'org.litepal.android:core:1.6.1'
```

**创建litepal.xml**

在main文件夹下创建一下assets文件夹，然后创建litepal.xml文件：

```
<?xml version="1.0" encoding="utf-8"?>
<litepal>
    <dbname value="DataBase" />

    <version value="1"/>

    <list>
        <mapping class="com.mezzsy.client.bean.MeizhiBean"/>
    </list>
</litepal>
```

dbname表示数据库名字，version表示版本，list里声明bean类，每次变更数据库需要版本号+1。

**初始化**

然后在Application中初始化

```
LitePal.initialize(context);
```

**创建数据库**

```
LitePal.getDatabase();
```

**添加数据**

Bean类需要继承DataSupport,然后调用一下save方法就可以实现保存。更新数据也是用save方法。

**查询数据**

这样写：

```
List<Book> books = DataSupport.findAll(Book.class);
```

```
List<UserBean> userBeans= DataSupport
        .select("name")
        .where("name = ?",userName).find(UserBean.class);
```

## 分析

### **初始化**

```kotlin
@JvmStatic fun initialize(context: Context) {
    LitePalApplication.sContext = context
}
```

在应用的Application中声明的，使LitePal获得Application的context。

### **创建数据库**

```
@JvmStatic fun getDatabase(): SQLiteDatabase {
    synchronized(LitePalSupport::class.java) {
        return Connector.getDatabase()
    }
}
```

```
public static SQLiteDatabase getDatabase() {
   return getWritableDatabase();
}
```

```
public synchronized static SQLiteDatabase getWritableDatabase() {
   LitePalOpenHelper litePalHelper = buildConnection();
   return litePalHelper.getWritableDatabase();
}
```

LitePalOpenHelper继承了SQLiteOpenHelper，用来创建数据库的帮助类，然后用这个对象的getWritableDatabase方法创建数据库，这个和SQLite的操作相同。

由此可以看出，LitePal实际上封装了SQLite操作，可以按着SQLite的思路来分析LitePal。

```java
private static LitePalOpenHelper buildConnection() {
   LitePalAttr litePalAttr = LitePalAttr.getInstance();
   //。。。
   return mLitePalHelper;
}
```

```
LitePalAttr litePalAttr = LitePalAttr.getInstance();
```

返回一个LitePalAttr的单例对象。

```
public static LitePalAttr getInstance() {
   if (litePalAttr == null) {
      synchronized (LitePalAttr.class) {
         if (litePalAttr == null) {
            litePalAttr = new LitePalAttr();
                   loadLitePalXMLConfiguration();
         }
      }
   }
   return litePalAttr;
}

private static void loadLitePalXMLConfiguration() {
       if (BaseUtility.isLitePalXMLExists()) {
           LitePalConfig config = LitePalParser.parseLitePalConfiguration();
           litePalAttr.setDbName(config.getDbName());
           litePalAttr.setVersion(config.getVersion());
           litePalAttr.setClassNames(config.getClassNames());
           litePalAttr.setCases(config.getCases());
           litePalAttr.setStorage(config.getStorage());
       }
   }
```

```
LitePalConfig config = LitePalParser.parseLitePalConfiguration();
```

```
public static LitePalConfig parseLitePalConfiguration() {
   if (parser == null) {
      parser = new LitePalParser();
   }
   return parser.usePullParse();
}
```

```
private LitePalConfig usePullParse() {
   try {
      LitePalConfig litePalConfig = new LitePalConfig();
      XmlPullParserFactory factory = XmlPullParserFactory.newInstance();
      XmlPullParser xmlPullParser = factory.newPullParser();
      xmlPullParser.setInput(getConfigInputStream(), "UTF-8");
      int eventType = xmlPullParser.getEventType();
      //。。。。
}
```

从这些命名就可以看出，用pull解析方式来解析assets文件夹下的litepal.xml，然后将内容放入LitePalConfig对象，然后从这个对象将所有属性读入litePalAttr模型以供使用。

获取到属性就可以根据属性来创建数据库了：

```
private static LitePalOpenHelper buildConnection() {
   LitePalAttr litePalAttr = LitePalAttr.getInstance();
   litePalAttr.checkSelfValid();
   if (mLitePalHelper == null) {
      String dbName = litePalAttr.getDbName();
      if ("external".equalsIgnoreCase(litePalAttr.getStorage())) {
         dbName = LitePalApplication.getContext().getExternalFilesDir("") + "/databases/" + dbName;
      } else if (!"internal".equalsIgnoreCase(litePalAttr.getStorage()) && !TextUtils.isEmpty(litePalAttr.getStorage())) {
               // internal or empty means internal storage, neither or them means sdcard storage
               String dbPath = Environment.getExternalStorageDirectory().getPath() + "/" + litePalAttr.getStorage();
               dbPath = dbPath.replace("//", "/");
               if (BaseUtility.isClassAndMethodExist("android.support.v4.content.ContextCompat", "checkSelfPermission") &&
                       ContextCompat.checkSelfPermission(LitePalApplication.getContext(), Manifest.permission.WRITE_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED) {
                   throw new DatabaseGenerateException(String.format(DatabaseGenerateException.EXTERNAL_STORAGE_PERMISSION_DENIED, dbPath));
               }
               File path = new File(dbPath);
               if (!path.exists()) {
                   path.mkdirs();
               }
               dbName = dbPath + "/" + dbName;
           }
      mLitePalHelper = new LitePalOpenHelper(dbName, litePalAttr.getVersion());
   }
   return mLitePalHelper;
}
```

如果是内部存储，那么数据库会存在/data/data/<package name\>/databases/ 目录下，数据库名为用户设定的名字。

如果是外部存储，那么会先申明权限，然后在存入相应的位置。

这样Helper对象就创建完了，然后调用getWritableDatabase方法创建数据库，这样数据库就创建成功。

### 更新数据库

更新同理：

```
override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
    Generator.upgrade(db)
    SharedUtil.updateVersion(LitePalAttr.getInstance().extraKeyName, newVersion)
    LitePal.getDBListener()?.onUpgrade(oldVersion, newVersion)
}
```

```
static void upgrade(SQLiteDatabase db) {
   drop(db);
   create(db, false);
   updateAssociations(db);
   upgradeTables(db);
   addAssociation(db, false);
}
```

从名字就可以看出，先把表丢掉，然后再创建表，和操作SQLite相似。

### 建表

getWritableDatabase方法后回调用helper的onCreate方法：

```
override fun onCreate(db: SQLiteDatabase) {
    Generator.create(db)
    LitePal.getDBListener()?.onCreate()
}
```

看看Generator.create(db)

```
static void create(SQLiteDatabase db) {
   create(db, true);
   addAssociation(db, true);
}
```

基于LITPEAL.XML文件中定义的类模型创建表。在创建表之后，基于类模型之间的关联将关联添加到这些表中。

LitePal采用的是**对象关系映射模型（ORM）**的模式，从这里就可以体现出了。

> 什么是对象关系映射模型?
>
> 我们使用的编程语言是面向对象的语言，而使用的数据库则是关系型数据库，将面向对象的语言和面向关系的数据库建立一种映射关系，这就是对象关系映射。
>
> 通过这种模式，可以用面向对象的思想去操作数据库，而不需要使用SQL语句了。

先建表 create(db, true); ：

```
private static void create(SQLiteDatabase db, boolean force) {
   Creator creator = new Creator();
   creator.createOrUpgradeTable(db, force);
}
```

```
protected void createOrUpgradeTable(SQLiteDatabase db, boolean force) {
   for (TableModel tableModel : getAllTableModels()) {
      createOrUpgradeTable(tableModel, db, force);
   }
}

   protected void createOrUpgradeTable(TableModel tableModel, SQLiteDatabase db, boolean force) {
       execute(getCreateTableSQLs(tableModel, db, force), db);
       giveTableSchemaACopy(tableModel.getTableName(), Const.TableSchema.NORMAL_TABLE, db);
   }
```

先看这个getAllTableModels方法：

```
protected Collection<TableModel> getAllTableModels() {
   if (mTableModels == null) {
      mTableModels = new ArrayList<TableModel>();
   }
   if (!canUseCache()) {
      mTableModels.clear();
      for (String className : LitePalAttr.getInstance().getClassNames()) {
         mTableModels.add(getTableModel(className));
      }
   }
   return mTableModels;
}
```

获取LitePalAttr中的类名，传入getTableModel(className)方法：

```java
protected TableModel getTableModel(String className) {
   String tableName = DBUtility.getTableNameByClassName(className);
   TableModel tableModel = new TableModel();
   tableModel.setTableName(tableName);
   tableModel.setClassName(className);
   List<Field> supportedFields = getSupportedFields(className);
   for (Field field : supportedFields) {
           ColumnModel columnModel = convertFieldToColumnModel(field);
           tableModel.addColumnModel(columnModel);
   }
   return tableModel;
}
```

这里用反射将对象的属性传入TableModel里，留到后面建表用。

继续看，在execute方法中有个方法getCreateTableSQLs方法

```java
protected List<String> getCreateTableSQLs(TableModel tableModel, SQLiteDatabase db, boolean force) {
       List<String> sqls = new ArrayList<String>();
   if (force) {
           sqls.add(generateDropTableSQL(tableModel));
           sqls.add(generateCreateTableSQL(tableModel));
   } else {
      if (DBUtility.isTableExists(tableModel.getTableName(), db)) {
         return null;
      } else {
               sqls.add(generateCreateTableSQL(tableModel));
      }
   }
       return sqls;
}
```

sqls.add(generateCreateTableSQL(tableModel));

这里是建表逻辑的真正实现：

```java
protected String generateCreateTableSQL(String tableName, List<ColumnModel> columnModels,
      boolean autoIncrementId) {
   StringBuilder createTableSQL = new StringBuilder("create table ");
   createTableSQL.append(tableName).append(" (");
   if (autoIncrementId) {
      createTableSQL.append("id integer primary key autoincrement,");
   }
   if (isContainsOnlyIdField(columnModels)) {
           // Remove the last comma when only have id field in model.
      createTableSQL.deleteCharAt(createTableSQL.length() - 1);
   }
   boolean needSeparator = false;
       for (ColumnModel columnModel : columnModels) {
           if (columnModel.isIdColumn()) {
               continue;
           }
           if (needSeparator) {
               createTableSQL.append(", ");
           }
           needSeparator = true;
           createTableSQL.append(columnModel.getColumnName()).append(" ").append(columnModel.getColumnType());
           if (!columnModel.isNullable()) {
               createTableSQL.append(" not null");
           }
           if (columnModel.isUnique()) {
               createTableSQL.append(" unique");
           }
           String defaultValue = columnModel.getDefaultValue();
           if (!TextUtils.isEmpty(defaultValue)) {
               createTableSQL.append(" default ").append(defaultValue);
           }
       }
   createTableSQL.append(")");
   LogUtil.d(TAG, "create table sql is >> " + createTableSQL);
   return createTableSQL.toString();
}
```

默认带有id属性（integer型）并作为主键，是否自增可以设置，默认自增。然后将TableModel中的列属性写入建表语句中，最后返回建表的SQL语句。

另外从这里可以看出，对象中可以不带有id属性，如果要有，不能将id设为其他属性。

然后再来看execute方法：

```java
protected void execute(List<String> sqls, SQLiteDatabase db) {
   String throwSQL = "";
   try {
      if (sqls != null && !sqls.isEmpty()) {
         for (String sql : sqls) {
                   if (!TextUtils.isEmpty(sql)) {
                       throwSQL = BaseUtility.changeCase(sql);
                       db.execSQL(throwSQL);
                   }
         }
      }
   } catch (SQLException e) {
      throw new DatabaseGenerateException(DatabaseGenerateException.SQL_ERROR + throwSQL);
   }
}
```

db.execSQL(throwSQL)执行建表语句，表创建成功。

```
static void create(SQLiteDatabase db) {
   create(db, true);
   addAssociation(db, true);
}
```

create分析完，再来看看addAssociation方法，这个方法正是基于类模型之间的关联向所有表添加关联：

```
private static void addAssociation(SQLiteDatabase db, boolean force) {
   AssociationCreator associationsCreator = new Creator();
   associationsCreator.addOrUpdateAssociation(db, force);
}
```

```
@Override
protected void addOrUpdateAssociation(SQLiteDatabase db, boolean force) {
   addAssociations(getAllAssociations(), db, force);
}
```

看看getAllAssociations()方法

```
protected Collection<AssociationsModel> getAllAssociations() {
   if (mAllRelationModels == null || mAllRelationModels.isEmpty()) {
      mAllRelationModels = getAssociations(LitePalAttr.getInstance().getClassNames());
   }
   return mAllRelationModels;
}
```

```
protected Collection<AssociationsModel> getAssociations(List<String> classNames) {
   if (mAssociationModels == null) {
      mAssociationModels = new HashSet<AssociationsModel>();
   }
       if (mGenericModels == null) {
           mGenericModels = new HashSet<GenericModel>();
       }
   mAssociationModels.clear();
       mGenericModels.clear();
   for (String className : classNames) {
      analyzeClassFields(className, GET_ASSOCIATIONS_ACTION);
   }
   return mAssociationModels;
}
```

analyzeClassFields方法将类中的变量封装成AssociationsModel，并存进mAssociationModels里。

分析集合中的所有关联模型。判断它们的关联类型。如果是one2one或many2one关联，到相关表添加外键列。如果是many2many协会，创建一个中间连接表。由于之前我们已经接触过建表的过程，所以这里就只看看在建表或者添加外键的前期处理。

### CRUD

添加数据一般是通过继承DataSupport，然后再CRUD的，但是一看DataSupport的注释：

```java
/**
 * DataSupport is deprecated and will be removed in the future release.
 * For model inheritance, use {@link LitePalSupport} instead.
 * For static CRUD op, use {@link LitePal} instead.
 *
 * @author Tony Green
 * @since 1.1
 */
```

被丢弃了。注释说继承的话用LitePalSupport，进行CRUD的话用LitePal。那么就看看这两个类：

LitePalSupport.java，这个类可以对对象进行CRUD。

#### 添加Create

```java
public boolean save() {
       try {
           saveThrows();
           return true;
       } catch (Exception e) {
           e.printStackTrace();
           return false;
       }
}
```

```java
public SaveExecutor saveAsync() {
    final SaveExecutor executor = new SaveExecutor();
    Runnable runnable = new Runnable() {
        @Override
        public void run() {
            synchronized (LitePalSupport.class) {
                final boolean success = save();
                if (executor.getListener() != null) {
                    LitePal.getHandler().post(new Runnable() {
                        @Override
                        public void run() {
                            executor.getListener().onFinish(success);
                        }
                    });
                }
            }
        }
    };
    executor.submit(runnable);
    return executor;
}
```

封装成一个Runnable对象，然后交给SaveExecutor处理。

#### 查询Retrieve

#### 更新Update

#### 删除Delete