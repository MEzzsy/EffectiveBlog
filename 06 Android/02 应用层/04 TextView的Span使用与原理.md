# 一个简单的 Demo

```kotlin
import android.app.Activity
import android.graphics.Color
import android.os.Bundle
import android.text.SpannableString
import android.text.Spanned
import android.text.method.LinkMovementMethod
import android.text.style.ClickableSpan
import android.text.style.DynamicDrawableSpan
import android.text.style.ImageSpan
import android.view.View
import android.widget.TextView
import android.widget.Toast
import kotlin.math.roundToInt

class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val textView = TextView(this).apply {
            textSize = 18f
            setTextColor(Color.DKGRAY)
            setLinkTextColor(Color.rgb(25, 100, 210))
            val padding = dp(24)
            setPadding(padding, padding, padding, padding)
        }

        // \uFFFC 是对象替换字符，用一个字符作为图片的占位。
        val content = "点击查看协议，旁边有张图片 \uFFFC"
        val richText = SpannableString(content)

        val linkText = "查看协议"
        val linkStart = content.indexOf(linkText)
        richText.setSpan(
            object : ClickableSpan() {
                override fun onClick(widget: View) {
                    Toast.makeText(widget.context, "点击了协议", Toast.LENGTH_SHORT).show()
                }
            },
            linkStart,
            linkStart + linkText.length,
            Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
        )

        val drawable = requireNotNull(
            getDrawable(android.R.drawable.btn_star_big_on)
        ).mutate()
        val imageSize = dp(24)
        drawable.setBounds(0, 0, imageSize, imageSize)

        val imageStart = content.indexOf('\uFFFC')
        richText.setSpan(
            ImageSpan(drawable, DynamicDrawableSpan.ALIGN_BASELINE),
            imageStart,
            imageStart + 1,
            Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
        )

        textView.text = richText
        textView.movementMethod = LinkMovementMethod.getInstance()
        setContentView(textView)
    }

    private fun dp(value: Int): Int =
        (value * resources.displayMetrics.density).roundToInt()
}
```

预期效果：

- “查看协议”呈现蓝色和下划线，点击后弹出 Toast。
- 文末的占位字符显示为一张 `24dp × 24dp` 的星星图片，图片本身暂时没有点击行为。

Demo 中有两个关键配置：`LinkMovementMethod` 负责识别链接点击；`Drawable.setBounds()` 指定图片在文本中的尺寸，参数单位为 px，所以先将 dp 换算为 px。

# Span 如何附着在文字上

可以把 Span 理解为：**给一段文本范围附加一个对象，让文本系统在测量、绘制或交互时使用它。** 对象和文字是两部分，添加 Span 不会直接把原始字符串改成图片或 View。

```kotlin
richText.setSpan(span, start, end, flags)
```

- `span`：效果或行为对象，例如 `ClickableSpan`、`ImageSpan`。
- `start`、`end`：作用范围为 `[start, end)`，包含起点，不包含终点。
- `flags`：控制文本在边界处插入内容时，Span 范围如何调整。`SPAN_EXCLUSIVE_EXCLUSIVE` 表示在两端插入的内容都不纳入原 Span；它不是控制点击区域的开关。

常见文本容器的区别如下：

| 类型 | 能否修改字符内容 | 能否添加、移除 Span |
| --- | --- | --- |
| `SpannedString` | 不能 | 不能 |
| `SpannableString` | 不能 | 能 |
| `SpannableStringBuilder` | 能 | 能 |

# 🌟ClickableSpan

## 绘制流程

- TextPaint 是用于测量和绘制文字的画笔，继承自 `Paint`。
  - 提供文字颜色、字号、字体、下划线等绘制属性。
  - Span 可以修改 TextPaint，让不同文字片段使用不同样式。

- Layout 负责文字的排版，并组织文字绘制。
  - TextView 绘制时，Layout 根据排版结果逐行绘制，复杂的行内样式交给 TextLine 处理。

整体流程：

1. `TextView.onDraw()` 会将文字绘制交给 `Layout`。
   - Layout 根据排版结果，确定每行文字的位置和基线。
   - 判断是否有 Span ？
     - Layout 用 `text instanceof Spanned` 判断。`SpannableString` 等类型会进入 TextLine，再检查具体有哪些样式 Span。
   - 对带有 Span 的文字，调用 `TextLine` 处理行内样式和绘制。
   - 非 Span 文字。排版简单时，直接调用 `Canvas.drawText()`；有双向文字、制表符等复杂情况时，也交给 TextLine，但跳过 Span 样式处理。
2. TextLine 会按照 Span 的起止位置划分文字片段。
   - 每个片段先从基础画笔复制出工作画笔。
   - 找到作用于该片段的 Span，调用它的 `updateDrawState()`。
   - ClickableSpan 在这个方法中调用 `setUnderlineText(true)`，给工作画笔设置下划线标记，此时还没有绘制下划线。
3. TextLine 提取并清除画笔的下划线标记，保存对应文字范围。
4. 先绘制文字，再根据文字范围和字体信息计算下划线的位置、长度与粗细。
5. 最后调用 `Canvas.drawRect()`，用文字颜色画一个窄矩形作为下划线。

## onClick响应

- `LinkMovementMethod` 负责识别文字中的链接点击，**需要设置给 TextView**。
- `Layout` 保存排版结果，可以根据触摸坐标查找对应的字符位置。

整体流程：

1. 触摸事件到达 `TextView.onTouchEvent()`。
   - TextView 将事件交给配置好的 `LinkMovementMethod.onTouchEvent()`。
2. LinkMovementMethod 将触摸坐标转换为文本坐标。
3. 根据文本坐标查找 ClickableSpan。
   - `Layout.getLineForVertical(y)`：找到所在行。
   - `Layout.getOffsetForHorizontal(line, x)`：找到字符位置。
   - `buffer.getSpans(offset, offset, ClickableSpan.class)`：查询该位置的 ClickableSpan。
4. 手指按下，即 `ACTION_DOWN` 时：
   - 如果命中 Span，调用 `Selection.setSelection()` 选中其文字范围。
   - TextView 根据选区绘制按下时的背景高亮。
5. 手指抬起，即 `ACTION_UP` 时：
   - 根据抬起位置重新查找 Span。
   - 如果命中，调用 `span.onClick(textView)`，执行业务回调。

# ImageSpan

## 测量

🌟总结：在TextView的onMeasure阶段会基于ImageSpan的Drawable的bounds来计算宽高。

1. `TextView.onMeasure()` 确定文字可用宽度，并按需创建或更新文本 Layout。
   - 可用宽度通常是 TextView 宽度减去左右 padding。
   - Layout 负责计算文字换行、行高和基线。
2. 测量文字时，发现 ImageSpan 属于 ReplacementSpan，就调用其 `getSize()`。
   - **返回图片的占位宽度**。
   - 通过 `FontMetricsInt` 提供图片所需的垂直空间。
   - 这些尺寸来自 Drawable 的 bounds，不再按被替换字符的字形计算。
3. 文本 Layout 将图片尺寸纳入排版。
   - 图片宽度参与换行计算，并影响后续文字的位置。
   - 图片高度与同一行文字的字体度量共同决定行高，因此大图片可能撑高整行。

## 绘制

🌟总结：在TextView的onDraw阶段识别出ImageSpan（实际识别的是ReplacementSpan），调用其draw方法。内部会调用 `Drawable.draw(canvas)` 绘制图片。

- ImageSpan 将指定范围的文字显示为图片，底层文字内容仍然保留。
  - 继承关系为 `ImageSpan → DynamicDrawableSpan → ReplacementSpan`。
  - ImageSpan 负责提供 Drawable，DynamicDrawableSpan 实现图片的测量和绘制。
- ReplacementSpan 允许接管一段文字的测量和绘制。
  - `getSize()`：返回占位宽度，并通过字体度量提供所需的垂直空间。
  - `draw()`：在排版分配的位置绘制内容。

整体流程：

1. 创建 ImageSpan，并通过 `setSpan()` 将它附加到文字范围。
   - 可以用 `\uFFFC` 作为图片占位字符。
     - `\uFFFC` 是 Unicode 的对象替换字符，常用来在文本中给图片等对象占一个位置。
   - 直接传入 Drawable 时，需要设置有效的 `bounds`，例如 `setBounds(0, 0, width, height)`，尺寸单位为 px。
2. 文本测量时，排版系统发现 ReplacementSpan，调用它的 `getSize()`。
   - ImageSpan 使用父类 DynamicDrawableSpan 的实现，根据 Drawable 的 bounds 提供尺寸。
   - 对于上述从 `(0, 0)` 开始的 bounds，返回图片宽度，并通过 `FontMetricsInt` 提供图片所需的高度信息。
3. Layout 根据图片占位和其他文字的尺寸完成排版。
   - 确定换行、行高，以及图片在行中的位置。
   - 图片较高时可能撑高整行，较宽时可能影响换行。
4. `TextView.onDraw()` 将文字绘制交给 Layout，再由 TextLine 处理行内内容。
   - TextLine 识别出 ImageSpan 属于 ReplacementSpan，调用其 `draw()`。
   - 此时绘制该范围的图片，不再绘制原来的占位字符。
5. DynamicDrawableSpan 的 `draw()` 将 Drawable 绘制到对应位置。
   - 保存 Canvas 状态，根据行位置和对齐方式计算图片的纵向偏移。
   - 调用 `Canvas.translate()`，将画布原点移动到图片的绘制位置。
   - 调用 `Drawable.draw(canvas)` 绘制图片，再恢复 Canvas 状态。
