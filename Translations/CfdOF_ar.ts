<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1">
<context>
    <name>App::Property</name>
    <message>
        <location filename="../CfdOF/CfdAnalysis.py" line="68"/>
        <source>Path to which cases are written (blank to use system default; relative path is relative to location of current file)</source>
        <translation>المسار الذي ستكتب فيه الحالات</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdAnalysis.py" line="76"/>
        <source>Active analysis object in document</source>
		<translation>الحالة النشطة في المستند</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdAnalysis.py" line="85"/>
        <source>Mesh setup needs to be re-written</source>
		<translation>اعداد الشبكة يحتاج اعادة كتابة</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdAnalysis.py" line="93"/>
        <source>Case setup needs to be re-written</source>
		<translation>اعداد الحالة يحتاج اعادة كتابة</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdAnalysis.py" line="101"/>
        <source>Mesher needs to be re-run before running solver</source>
        <translation>يحتاج الميشر لأعادة البدا قبل ان يبدا المحلل</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdAnalysis.py" line="109"/>
        <source>Use a hostfile for parallel cluster runs</source>
        <translation>استخدم ملف استضافة للتشغيل على التوازي في خادم</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdAnalysis.py" line="117"/>
        <source>Hostfile name</source>
		<translation>اسم ملف الاستضافة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="104"/>
        <source>Name of directory in which the mesh is created</source>
		<translation>اسم المجلد الذي ستصنع فيه الميش</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="117"/>
        <source>Maximum relative linear deflection for built-in surface triangulation</source>
		<translation>اقصى انحراف نسبي خطي لتثليث السطح المضمن</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="127"/>
        <source>Mesh elements per 360 degrees for surface triangulation with GMSH</source>
		<translation>عدد عناصر الميش في كل 360 درجة لتثليث الاصطح لGMSH</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="139"/>
        <source>Number of parallel processes (only applicable to cfMesh and snappyHexMesh)</source>
		<translation>عدد العمليات المتوازية (قابلة للتطبيق فقط في cfMesh و snappyHexMesh)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="152"/>
        <source>Number of parallel threads per process (only applicable to cfMesh and gmsh).
0 means use all available (if NumberOfProcesses = 1) or use 1 (if NumberOfProcesses &gt; 1)</source>
		<translation>عدد المسارات المتوازية في كل عملية (قابلة للتطبيق فقط في cfMesh و gmsh).
0 تعني استخدام كل المتاح (اذا كان NumberOfProcesses = 1) او استخدم 1 (اذا NumberOfProcesses &gt; 1)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="161"/>
        <source>Part object to mesh</source>
		<translation>جزء القطعة الذ ستطبق فيه الميش</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="170"/>
        <source>Meshing utilities</source>
        <translation>الادوات المساعدة في عملية الميش</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="181"/>
        <source>Max mesh element size (0.0 = infinity)</source>
		<translation>اقصى حجم للعنصر في الميش (0.0 = ما لا نهاية)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="193"/>
        <source>Location vector inside the region to be meshed (must not coincide with a cell face)</source>
		<translation>متجه الموقع داخل المنطقة المراد عمل الميش عليها (يجب ان لا تقع على وجه خلية)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="202"/>
        <source>Number of cells between each level of refinement</source>
		<translation>عدد الخلايا بين كل مستوى تصغير</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="211"/>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="186"/>
        <source>Relative edge (feature) refinement</source>
		<translation>التصغير بالنسبة للحواف (الخواص)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="221"/>
        <source>Convert to polyhedral dual mesh</source>
		<translation>حول الى ميش مزدوجة متعددة السطوح</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="231"/>
        <source>Use implicit edge detection</source>
		<translation>استخدم كشف الحواف الضمني</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="241"/>
        <source>Dimension of mesh elements (Default 3D)</source>
		<translation>ابعاد عناصر الميش (الافتراضي 3D)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="202"/>
        <source>Set the target refinement interface phase</source>
		<translation>اضبط الطور لهدف واجهة التصغير</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="214"/>
        <source>Set the interval at which to run the dynamic mesh refinement</source>
		<translation>اضبط الفترة التي سيعمل فيها التصغير الديناميكي للميش</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="223"/>
        <source>Set the maximum dynamic mesh refinement level</source>
		<translation>اضبط اقصى مستوى تصغير ديناميكي للميش</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="235"/>
        <source>Set the number of buffer layers between refined and existing cells</source>
		<translation>اضبط عدد طبقات الحاجز بين الخلايا المصغرة و الموجودة مسبقا</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="247"/>
        <source>Whether to write the dynamic mesh refinement fields after refinement</source>
		<translation>هل يكتب حقل التصغير الديناميكي للميش بعد التصغير</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="283"/>
        <source>Reference velocity direction (typically free-stream/input value)</source>
		<translation>اتجاه السرعة المرجعية (عادتا التدفق الحر او القيمة المدخلة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="292"/>
        <source>Refinement relative to the base mesh</source>
		<translation>التصغير بانسة للميش الاصلية</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="304"/>
        <source>Interval at which to run the dynamic mesh refinement in steady analyses</source>
		<translation>الفترة التي يشتغل فيها التصغير الديناميكي للميش في التحليلات الثابتة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="316"/>
        <source>Interval at which to run the dynamic mesh refinement in transient analyses</source>
		<translation>الفترة التي يشتغل فيها التصغير الديناميكي للميش في التحليلات المتغيرة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="328"/>
        <source>Number of buffer layers between refined and existing cells</source>
		<translation>عدد طبقات الحواجز بين التصغير و الخلايا الموجودة مسبقا</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="340"/>
        <source>Whether to write the indicator fields for shock wave detection</source>
		<translation>هل يكتب الحقل الذي يشير الى موجات الصدمة المكتشفة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="100"/>
        <source>List of mesh refinement objects</source>
		<translation>قائمة الاشياء التي سيطبق عليها التصغير</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="121"/>
        <source>Whether the refinement region is a volume rather than surface</source>
		<translation>ما اذا كانت منطقة التصغير حجم بدلا عن سطح</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="130"/>
        <source>Defines an extrusion from a patch</source>
		<translation>عرف البثق عبر حد</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="141"/>
        <source>Set relative length of the elements for this region</source>
		<translation>اضبط الطول النسبي للعناصر في هذه المنطقة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="150"/>
        <source>Set refinement region thickness</source>
		<translation>اضبط سمك تصغير المنطقة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="159"/>
        <source>Set number of boundary layers</source>
		<translation>اضبط عدد طبقات الحدود</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="168"/>
        <source>Set expansion ratio within boundary layers</source>
		<translation>اضبط نسبة التمدد في طبقات الحدود</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="177"/>
        <source>Set the maximum first layer height</source>
		<translation>اضبط اقصى ارتفاع في الطبقة الاولا</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="195"/>
        <source>Type of extrusion</source>
		<translation>نوع البثق</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="207"/>
        <source>If true, then the extrusion extends the existing mesh rather than replacing it</source>
		<translation>اذا صح, البثق يمد الميش الموجودة بدل ان يستبدلها</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="216"/>
        <source>Total distance of the extruded layers</source>
		<translation>المسافة الكلية للطبقات الممتدة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="225"/>
        <source>Total angle through which the patch is extruded</source>
		<translation>الزاوية التي ستميد في اتجاهها الحدود</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="234"/>
        <source>Number of extrusion layers to add</source>
		<translation>عدد طبقات التمدد لاضافتها</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="243"/>
        <source>Expansion ratio of extrusion layers</source>
		<translation>نسبة التمدد في الطبقات</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="252"/>
        <source>Point on axis for sector extrusion</source>
		<translation>نقطة في محور لبثق القطاع</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="261"/>
        <source>Direction of axis for sector extrusion</source>
		<translation>اتجاه المحور لبثق القطاع</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="93"/>
        <source>Type of reporting function</source>
		<translation>نوع دالة التقرير</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="102"/>
        <source>Patch on which to create the function object</source>
		<translation>الحدود التي سيصنع فيها دالة القطعة</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="112"/>
        <source>Reference density</source>
		<translation>الكثافة المرجعية</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="120"/>
        <source>Reference pressure</source>
		<translation>الضغط المرجعي</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="128"/>
        <source>Centre of rotation</source>
		<translation>مركز الدوران</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="136"/>
        <source>Whether to write output fields</source>
		<translation>ما اذا كان سيكتب حقل الناتج</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="146"/>
        <source>Lift direction (x component)</source>
		<translation>اتجاه الرفع (المكون س)</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="155"/>
        <source>Drag direction</source>
		<translation>اتجاه الجر</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="164"/>
        <source>Freestream velocity magnitude</source>
		<translation>القيمة المطلقة لسرعة التيار الحر</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="172"/>
        <source>Coefficient length reference</source>
		<translation>معامل الطول المرجعي</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="180"/>
        <source>Coefficient area reference</source>
		<translation>معامل المساحة المرجعية</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="190"/>
        <source>Number of bins</source>
		<translation>عدد النقات المثبتة</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="198"/>
        <source>Binning direction</source>
		<translation>اتجاه التثبيت</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="206"/>
        <source>Cumulative</source>
		<translation>التراكمي</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="216"/>
        <source>Name of the field to sample</source>
		<translation>اسم الحقل المراد قياسه</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="225"/>
        <source>Location of the probe sample</source>
		<translation>موقع عينة المجس</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="324"/>
        <location filename="../CfdOF/Solve/CfdZone.py" line="121"/>
        <source>Boundary faces</source>
		<translation>اوجه الحدود</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="350"/>
        <source>Boundary condition category</source>
		<translation>فئة حالة الحدود</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="363"/>
        <source>Boundary condition type</source>
		<translation>نوع حالة الحدود</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="371"/>
        <source>Whether to use components of velocity</source>
		<translation>ما اذا كان سيستخدم مكونات السرعة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="379"/>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="127"/>
        <location filename="../CfdOF/Solve/CfdZone.py" line="281"/>
        <source>Velocity (x component)</source>
		<translation>السرعة (المكون س)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="387"/>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="135"/>
        <location filename="../CfdOF/Solve/CfdZone.py" line="289"/>
        <source>Velocity (y component)</source>
		<translation>السرعة (المكون ص)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="395"/>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="143"/>
        <location filename="../CfdOF/Solve/CfdZone.py" line="297"/>
        <source>Velocity (z component)</source>
		<translation>السرعة (المكون ع)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="403"/>
        <source>Velocity magnitude</source>
		<translation>القيمة المطلقة للسرعة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="411"/>
        <source>Face describing direction (normal)</source>
		<translation>وجه يصف الاتجاه (مقابل)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="419"/>
        <source>Direction is inward-pointing if true</source>
		<translation>الاتجاه سيكون مؤشر للداخل اذا كان صح</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="427"/>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="151"/>
        <location filename="../CfdOF/Solve/CfdZone.py" line="313"/>
        <source>Static pressure</source>
		<translation>الضغط الثابت</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="435"/>
        <source>Slip ratio</source>
		<translation>نسبة الانزلاق</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="443"/>
        <source>Volume flow rate</source>
		<translation>معدل تدفق الحجم</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="451"/>
        <source>Mass flow rate</source>
		<translation>معدل تدفق الكتلة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="460"/>
        <source>Relative velocity</source>
		<translation>السرعة النسبية</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="469"/>
        <source>Baffle</source>
		<translation>حاجز</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="479"/>
        <source>Porous baffle pressure drop coefficient</source>
		<translation>نسبة انخفاض الضغط في الحواجز المسامية</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="487"/>
        <source>Porous screen mesh diameter</source>
		<translation>قطر ميش الشاشة المسامية</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="495"/>
        <source>Porous screen mesh spacing</source>
		<translation>مسافة ميش الشاشة المسامية</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="504"/>
        <source>Sand-grain roughness</source>
		<translation>خشونة حبوب الرمل</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="512"/>
        <source>Coefficient of roughness [0.5-1]</source>
		<translation>معامل الخشونة َِْ[0.5-1]</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="521"/>
        <source>Type of thermal boundary</source>
		<translation>نوع الحد الحراري</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="529"/>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="167"/>
        <location filename="../CfdOF/Solve/CfdZone.py" line="329"/>
        <source>Temperature</source>
		<translation>الحرارة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="537"/>
        <source>Wall heat flux</source>
		<translation>تدفق حرارة الجدار</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="545"/>
        <source>Wall heat transfer coefficient</source>
		<translation>معامل انتقال حرارة الجدار</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="555"/>
        <source>Rotational or translational periodicity</source>
		<translation>تواترية دورانية او انتقالية</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="563"/>
        <source>Centre of rotation for rotational periodics</source>
		<translation>مركز الدوران للتواتر الدوراني</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="571"/>
        <source>Axis of rotational for rotational periodics</source>
		<translation>محور الدوران للتواتر الدوراني</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="579"/>
        <source>Separation vector for translational periodics</source>
		<translation>المتجه الفاصل للتواتر الانتقالي</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="587"/>
        <source>Partner patch for the slave periodic</source>
		<translation>تصحيح الحد للعبد التواتري</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="597"/>
        <source>Whether the current patch is the master or slave patch</source>
		<translation>ما اذا كان الحد الحالي عبد او سيد</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="613"/>
        <source>Turbulent quantities specified</source>
		<translation>الكميات الضطربة المحددة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="624"/>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="183"/>
        <source>Turbulent kinetic energy</source>
		<translation>الطاقة الحركية المضطربة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="632"/>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="191"/>
        <source>Specific turbulent dissipation rate</source>
		<translation>معدل تشتت الاضطراب المحدد</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="642"/>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="199"/>
        <source>Turbulent dissipation rate</source>
		<translation>معدل تشتت الاضطراب</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="652"/>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="207"/>
        <source>Modified turbulent viscosity</source>
		<translation>اللزوجة المضطربة المحددة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="662"/>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="215"/>
        <source>Turbulent intermittency</source>
		<translation>التقطع المضطرب</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="670"/>
        <source>Transition momentum thickness Reynolds number</source>
		<translation>سماكة الزخم الانتقالي لرقم رينولدز</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="680"/>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="688"/>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="696"/>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="231"/>
        <source>Turbulent viscosity</source>
		<translation>اللزوجة المضطربة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="706"/>
        <source>Turbulence intensity (percent)</source>
		<translation>القوة المضطربة (في المائة)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="719"/>
        <source>Length scale of turbulent eddies</source>
		<translation>مقياس طول الدوامات المضطربة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="727"/>
        <source>Volume fractions</source>
		<translation>جزء حجمي</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidMaterial.py" line="98"/>
        <source>List of material shapes</source>
		<translation>قائمة اشكال المواد</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidMaterial.py" line="108"/>
        <source>Type of material</source>
		<translation>نوع المادة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="95"/>
        <source>Initialise velocity with potential flow solution</source>
		<translation>تهيئة السرعة بحل التدفق المحتمل</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="103"/>
        <source>Initialise pressure with potential flow solution</source>
		<translation>تهيئة الضغط بحل التدفق المحتمل</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="111"/>
        <source>Initialise with flow values from inlet</source>
		<translation>تهيئة بقيم التدفق من المدخل</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="119"/>
        <source>Initialise with flow values from outlet</source>
		<translation>تهيئة بقيم التدفق من المخرج</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="159"/>
        <source>Initialise with temperature value from inlet</source>
		<translation>تهيئة بقيم الحرارة من المدخل</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="175"/>
        <source>Initialise turbulence with values from inlet</source>
		<translation>تهيئة الاضطراب بقيم من المدخل</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="223"/>
        <source>Transition Momentum Thickness Reynolds Number</source>
		<translation>سماكة الزخم الانتقالي لرقم رينولدز</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="240"/>
        <location filename="../CfdOF/Solve/CfdZone.py" line="345"/>
        <source>Volume fraction values</source>
		<translation>قيم الجزء الحجمي</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="248"/>
        <source>U boundary</source>
		<translation>حد U</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="256"/>
        <source>P boundary</source>
        <translation>حد P</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="264"/>
        <source>T boundary</source>
        <translation>حد T</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="272"/>
        <source>Turbulence boundary</source>
        <translation>حد الاضطراب</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdPhysicsSelection.py" line="114"/>
        <source>Resolve time dependence</source>
		<translation>حل يعتمد على الزمن</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdPhysicsSelection.py" line="130"/>
        <source>Flow algorithm</source>
		<translation>خوارزمية التدفق</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdPhysicsSelection.py" line="148"/>
        <source>Type of phases present</source>
		<translation>نوع الطور الموجود</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdPhysicsSelection.py" line="158"/>
        <source>Type of turbulence modelling</source>
		<translation>نوع نموذج الاضطراب</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdPhysicsSelection.py" line="182"/>
        <source>Turbulence model</source>
		<translation>نموذج الاضطراب</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdPhysicsSelection.py" line="193"/>
        <source>Gravitational acceleration vector (x component)</source>
		<translation>متجه عجلة الجاذبية (مكون س)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdPhysicsSelection.py" line="201"/>
        <source>Gravitational acceleration vector (y component)</source>
		<translation>متجه عجلة الجاذبية (مكون ص)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdPhysicsSelection.py" line="209"/>
        <source>Gravitational acceleration vector (z component)</source>
		<translation>متجه عجلة الجاذبية (مكون ع)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdPhysicsSelection.py" line="219"/>
        <source>Single Rotating Frame model enabled</source>
        <translation>تفعيل نموذج الاطار الدوار المفرد (Single Rotating Frame(SRF))</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdPhysicsSelection.py" line="228"/>
        <source>Rotational speed</source>
		<translation>السرعة الدورانية</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdPhysicsSelection.py" line="237"/>
        <source>Centre of rotation (SRF)</source>
        <translation>مركز الدوران (SRF)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdPhysicsSelection.py" line="246"/>
        <source>Axis of rotation (SRF)</source>
        <translation>محور الدوران (SRF)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdScalarTransportFunction.py" line="85"/>
        <source>Name of the scalar transport field</source>
		<translation>اسم حقل النقل العددي</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdScalarTransportFunction.py" line="96"/>
        <source>Use fixed value for diffusivity rather than viscosity</source>
		<translation>استخدم قيمة ثابتة للانتشار عوضا عن اللزوجة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdScalarTransportFunction.py" line="106"/>
        <source>Diffusion coefficient for fixed diffusivity</source>
		<translation>معامل الانتشار</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdScalarTransportFunction.py" line="115"/>
        <source>Restrict transport within phase</source>
		<translation>قيد التنقل في الطور</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdScalarTransportFunction.py" line="124"/>
        <source>Transport within phase</source>
        <translation>التنقل في الطور</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdScalarTransportFunction.py" line="133"/>
        <source>Injection rate</source>
		<translation>معدل الحقن</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdScalarTransportFunction.py" line="142"/>
        <source>Location of the injection point</source>
		<translation>مكان نقطة الحقن</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="96"/>
        <source>Name of case directory where the input files are written</source>
		<translation>اسم مجلد الادخال الذي ستكتب فيه ملفات الادخال</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="104"/>
        <source>Parallel analysis on multiple CPU cores</source>
		<translation>التحليل على التوازي على عدة انوية معالج</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="112"/>
        <source>Number of cores on which to run parallel analysis</source>
		<translation>عدد الانوية التي سيتم التحليل عليها على التوازي</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="123"/>
        <source>Sets a limit on the number of time directories that are stored by overwriting time directories on a cyclic basis.  Set to 0 to disable</source>
		<translation>ضبط حد لعدد مجلدات الزمن المخزنة عبر اعادة كتابة المجلدات دوريا. اضبطه 0 لايقافه</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="134"/>
        <source>Maximum number of iterations to run steady-state analysis</source>
		<translation>اقصى عدد تكرارات لتشغيل التحليل الثابت</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="142"/>
        <source>Iteration output interval</source>
		<translation>فترة اخراج التكرار</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="150"/>
        <source>Global absolute solution convergence criterion</source>
		<translation>معيار تقارب الحل المطلق العالمي</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="159"/>
        <source>Whether to restart or resume solving</source>
		<translation>هل يبدا من جديد او يستمر في التحليل</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="168"/>
        <source>Total time to run transient solution</source>
		<translation>الزمن الكلي لتشغيل الحل المتحرك</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="176"/>
        <source>Time step increment</source>
		<translation>زيادة الخطوة الزمنية</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="184"/>
        <source>Maximum CFL number for transient simulations</source>
		<translation>اقصى قيمة لرقم CFL للمحاكاة المتحركة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="194"/>
        <source>Maximum free-surface CFL number for transient simulations</source>
		<translation>اقصى قيمة لرقم CFL للسطح الحر للمحاكاة المتحركة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="202"/>
        <source>Output time interval</source>
		<translation>الفترة الزمنية للاخراج</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="141"/>
        <source>Porous drag model</source>
		<translation>نموذج السحب المسامي</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="150"/>
        <source>Darcy coefficient (direction 1)</source>
		<translation>معامل دارسي (اتجاه 1)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="158"/>
        <source>Darcy coefficient (direction 2)</source>
		<translation>معامل دارسي (اتجاه 2)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="166"/>
        <source>Darcy coefficient (direction 3)</source>
		<translation>معامل دارسي (اتجاه 3)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="174"/>
        <source>Forchheimer coefficient (direction 1)</source>
		<translation>معامل فوركايمر (اتجاه 1)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="182"/>
        <source>Forchheimer coefficient (direction 2)</source>
		<translation>معامل فوركايمر (اتجاه 2)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="190"/>
        <source>Forchheimer coefficient (direction 3)</source>
		<translation>معامل فوركايمر (اتجاه 3)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="198"/>
        <source>Principal direction 1</source>
		<translation>الاتجاه الرئيسي 1</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="206"/>
        <source>Principal direction 2</source>
		<translation>الاتجاه الرئيسي 2</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="214"/>
        <source>Principal direction 3</source>
		<translation>الاتجاه الرئيسي 3</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="222"/>
        <source>Tube diameter</source>
		<translation>قطر الانبوب</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="230"/>
        <source>Direction parallel to tubes</source>
		<translation>الاتجاه الموازي الانبوب</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="238"/>
        <source>Spacing between tube layers</source>
		<translation>المسافة بين طبقات الانبوب</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="246"/>
        <source>Direction normal to tube layers</source>
		<translation>الاتجاه المقابل لطبقات الانبوب</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="256"/>
        <source>Tube spacing aspect ratio (layer-to-layer : tubes in layer)</source>
		<translation>نسبة المسافة بين الانابيب (طبقة-الى-طبقة : انابيب في الطبقة)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="264"/>
        <source>Approximate flow velocity</source>
		<translation>تقريب سرعة التدفق</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="273"/>
        <source>Whether the zone initialises velocity</source>
		<translation>ما اذا كانت المنطقة تهيئ السرعة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="305"/>
        <source>Whether the zone initialises pressure</source>
		<translation>ما اذا كانت المنطقة تهيئ الضغط</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="321"/>
        <source>Whether the zone initialises temperature</source>
		<translation>ما اذا كانت المنطقة تهيئ الحرارة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="337"/>
        <source>Whether the zone initialises volume fraction</source>
		<translation>ما اذا كانت المنطقة تهيئ الجزء الحجمي</translation>
    </message>
</context>
<context>
    <name>Boundary</name>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="45"/>
        <source>Wall</source>
        <translation>جدار</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="46"/>
        <source>Inlet</source>
        <translation>مدخل</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="47"/>
        <source>Outlet</source>
        <translation>مخرج</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="48"/>
        <source>Open</source>
        <translation>مفتوح</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="49"/>
        <source>Constraint</source>
        <translation>قصر / Constraint</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="50"/>
        <source>Baffle</source>
        <translation>حاجز / Baffle</translation>
    </message>
</context>
<context>
    <name>CfdOF_Analysis</name>
    <message>
        <location filename="../CfdOF/CfdAnalysis.py" line="163"/>
        <source>Analysis container</source>
        <translation>حاوية التحليل</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdAnalysis.py" line="167"/>
        <source>Creates an analysis container with a CFD solver</source>
		<translation>اصنع حاوية تحليل مع محلل CFD</translation>
    </message>
</context>
<context>
    <name>CfdOF_DynamicMeshInterfaceRefinement</name>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="90"/>
        <source>Interface dynamic refinement</source>
		<translation>التصغير الديناميكي للواجهة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="95"/>
        <source>Activates adaptive mesh refinement at free-surface interfaces</source>
		<translation>تفعيل التصغير التكيفي في واجهات الاصطح الحرة</translation>
    </message>
</context>
<context>
    <name>CfdOF_DynamicMeshShockRefinement</name>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="143"/>
        <source>Shockwave dynamic refinement</source>
		<translation>التصغير الديناميكي لموجة الصدمة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="148"/>
        <source>Activates adaptive mesh refinement for shocks</source>
		<translation>تفعيل التصغير التكيفي للصدمات</translation>
    </message>
</context>
<context>
    <name>CfdOF_FluidBoundary</name>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="296"/>
        <source>Fluid boundary</source>
		<translation>حد مائع</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="300"/>
        <source>Creates a CFD fluid boundary</source>
		<translation>اصنع حد مائع CFD</translation>
    </message>
</context>
<context>
    <name>CfdOF_FluidMaterial</name>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidMaterial.py" line="54"/>
        <location filename="../CfdOF/Solve/CfdFluidMaterial.py" line="57"/>
        <source>Add fluid properties</source>
		<translation>اضف خصائص مائع</translation>
    </message>
</context>
<context>
    <name>CfdOF_GroupDynamicMeshRefinement</name>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="46"/>
        <source>Dynamic mesh refinement</source>
		<translation>التصغير الديناميكي</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="50"/>
        <source>Allows adaptive refinement of the mesh</source>
		<translation>السماح بالتصغير التكيفي</translation>
    </message>
</context>
<context>
    <name>CfdOF_InitialisationZone</name>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="90"/>
        <source>Initialisation zone</source>
		<translation>منطقة التهيئة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="95"/>
        <source>Select and create an initialisation zone</source>
		<translation>اختار و اصنع منطقة تهيئة</translation>
    </message>
</context>
<context>
    <name>CfdOF_InitialiseInternal</name>
    <message>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="54"/>
        <source>Initialise</source>
		<translation>هيئ</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="60"/>
        <source>Initialise internal flow variables based on the selected physics model</source>
		<translation>تهيئة متغيرات التدفق الداخلي بناءا على النموذج الفيزيائي المختار</translation>
    </message>
</context>
<context>
    <name>CfdOF_MeshFromShape</name>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="50"/>
        <source>CFD mesh</source>
		<translation>ميش الCFD</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="54"/>
        <source>Create a mesh using cfMesh, snappyHexMesh or gmsh</source>
		<translation>اصنع ميش باستخدام cfMesh او snappyHexMesh او gmsh</translation>
    </message>
</context>
<context>
    <name>CfdOF_MeshRegion</name>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="62"/>
        <source>Mesh refinement</source>
		<translation>تصغير الميش</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="66"/>
        <source>Creates a mesh refinement</source>
		<translation>اصنع تصغير ميش</translation>
    </message>
</context>
<context>
    <name>CfdOF_OpenPreferences</name>
    <message>
        <location filename="../CfdOF/CfdOpenPreferencesPage.py" line="33"/>
        <source>Open preferences</source>
		<translation>افتح التفضيلات</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdOpenPreferencesPage.py" line="36"/>
        <source>Opens the CfdOF preferences page</source>
		<translation>افتح صفحة تفضيلات CfdOF</translation>
    </message>
</context>
<context>
    <name>CfdOF_PhysicsModel</name>
    <message>
        <location filename="../CfdOF/Solve/CfdPhysicsSelection.py" line="54"/>
        <source>Select models</source>
		<translation>اختار النماذج</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdPhysicsSelection.py" line="58"/>
        <source>Select the physics model</source>
		<translation>اختار النموذج الفيزيائية</translation>
    </message>
</context>
<context>
    <name>CfdOF_PorousZone</name>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="70"/>
        <source>Porous zone</source>
		<translation>المنطقة المسامية</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="74"/>
        <source>Select and create a porous zone</source>
		<translation>اختار و اصنع منطقة مسامية</translation>
    </message>
</context>
<context>
    <name>CfdOF_ReloadWorkbench</name>
    <message>
        <location filename="../CfdOF/CfdReloadWorkbench.py" line="37"/>
        <source>Reload CfdOF workbench</source>
		<translation>اعادة تحميل منضد عمل CfdOF</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdReloadWorkbench.py" line="41"/>
        <source>Attempt to reload all CfdOF source files from disk. May break open documents!</source>
		<translation>محاولة لاعادة تحميل كل ملفات CfdOF المصدرية من القرص. ممكن يكسر المستندات المفتوحة</translation>
    </message>
</context>
<context>
    <name>CfdOF_ReportingFunctions</name>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="60"/>
        <source>Reporting function</source>
		<translation>دالة التقرير</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="64"/>
        <source>Create a reporting function for the current case</source>
		<translation>اصنع دالة تقرير للحالة الحالية</translation>
    </message>
</context>
<context>
    <name>CfdOF_ScalarTransportFunctions</name>
    <message>
        <location filename="../CfdOF/Solve/CfdScalarTransportFunction.py" line="53"/>
        <source>Cfd scalar transport function</source>
		<translation>دالة النقل العددي Cfd</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdScalarTransportFunction.py" line="57"/>
        <source>Create a scalar transport function</source>
		<translation>اصنع دالة النقل العددي</translation>
    </message>
</context>
<context>
    <name>CfdOF_SolverControl</name>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="55"/>
        <source>Solver job control</source>
		<translation>التحكم في وظيفة المحلل</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="59"/>
        <source>Edit properties and run solver</source>
		<translation>عدل الخصائص و شغل المحلل</translation>
    </message>
</context>
<context>
    <name>CfdPreferencePage</name>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="14"/>
        <source>General</source>
		<translation>عام</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="43"/>
        <location filename="../Gui/CfdPreferencePage.ui" line="99"/>
        <location filename="../Gui/CfdPreferencePage.ui" line="122"/>
        <location filename="../Gui/CfdPreferencePage.ui" line="129"/>
        <source>...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="50"/>
        <source>The full path to the gmsh executable. Leave blank to use the system search path.</source>
		<translation>المسار الكامل لبرنامج gmsh القابل للتنفيذ. اتركه فارغ لاستخدام مسار بحث النظام</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="60"/>
        <source>The full path of the ParaView executable. Leave blank to use system search path or default install locations.</source>
		<translation>المسار الكامل لبرنامج ParaView القابل للتنفيذ. اتركه فارغ لاستخدام مسار بحث النظام او موقع التثبيت الافتراضي</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="76"/>
        <source>OpenFOAM install directory</source>
		<translation>مجلد تثبيت OpenFOAM</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="89"/>
        <source>ParaView executable</source>
		<translation>برنامج paraview القابل للتنفيذ</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="109"/>
        <source>The OpenFOAM install folder. Leave blank to use $WM_PROJECT_DIR environment setting or standard install locations.</source>
		<translation>مجلد تثبيت OpenFOAM. اتركه خاليا لاستخدام المتغير البيئي $WM_PROJECT_DIR او موقع التثبيت المعياري</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="142"/>
        <source>gmsh executable</source>
		<translation>برنامج gmsh القابل للتنفيذ</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="155"/>
        <source>Default output directory</source>
		<translation>مجلد الاخراج الافتراضي</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="165"/>
        <source>The directory to which case folders are written. Used unless overridden on a per-analysis basis. Use a &apos;.&apos; to denote the location of the current saved document, or leave blank to use a temporary directory.</source>
		<translation>المجلد الذي سيكتب فيه مجلد الحالة. مستخدم مالم يستبدل لكل تحليل. استخدم &apos;.&apos; للاشارة الى موقع المستند المحفوظ حاليا, او اتركه خاليا لاستخدام مجلد مؤقت.</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="175"/>
        <source>Create the output in a subdirectory with the name of the current saved document.</source>
		<translation>اصنع مجلد فرعي للاخراج بنفس اسم المستند المحفوظ حلليا</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="178"/>
        <source>Append document name to output directory</source>
		<translation>الحق اسم المستند الى مجلد الاخراج</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="231"/>
        <source>Software dependencies</source>
		<translation>تبعيات البرامج</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="241"/>
        <source>Run dependency checker</source>
		<translation>تشغيل مدقق التبعية</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="263"/>
        <location filename="../Gui/CfdPreferencePage.ui" line="308"/>
        <location filename="../Gui/CfdPreferencePage.ui" line="373"/>
        <location filename="../Gui/CfdPreferencePage.ui" line="418"/>
        <source>Choose existing file ...</source>
		<translation>اختلر الملف الموجود ...</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="270"/>
        <source>Install OpenFOAM</source>
		<translation>ثبت OpenFOAM</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="283"/>
        <location filename="../Gui/CfdPreferencePage.ui" line="328"/>
        <location filename="../Gui/CfdPreferencePage.ui" line="353"/>
        <location filename="../Gui/CfdPreferencePage.ui" line="405"/>
        <source>URL:</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="315"/>
        <source>Install ParaView</source>
        <translation>ثبت ParaView</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="360"/>
        <source>Install cfMesh</source>
        <translation>ثبت cfMesh</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="392"/>
        <source>Install HiSA</source>
        <translation>ثبت HiSA</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="431"/>
        <source>Docker Container</source>
        <translation>حاوية Docker</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="437"/>
        <source>Use Docker:</source>
        <translation>استخدم Docker:</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="447"/>
        <source>Download from URL:</source>
        <translation>حمل منURL:</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="457"/>
        <source>Install Docker Image</source>
        <translation>ثبت صورة Docker</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="489"/>
        <source>Output</source>
        <translation>الاخراج</translation>
    </message>
</context>
<context>
    <name>Console</name>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidMaterial.py" line="61"/>
        <source>Set fluid properties 
</source>
		<translation>اضبط خواص المائع
</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdTools.py" line="1019"/>
        <source>Checking CFD workbench dependencies...
</source>
        <translation>جار التحقق من اعتماديات طاولة عمل CFD</translation>
    </message>
</context>
<context>
    <name>Dialogs</name>
    <message>
        <location filename="../CfdOF/Mesh/TaskPanelCfdMesh.py" line="294"/>
        <location filename="../CfdOF/CfdPreferencePage.py" line="302"/>
        <location filename="../CfdOF/CfdTools.py" line="364"/>
        <source>CfdOF Workbench</source>
        <translation>طاولة عمل CfdOF</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/TaskPanelCfdMesh.py" line="299"/>
        <source>The case setup for the mesher may need to be re-written based on changes you have made to the model.

Write mesh case first?</source>
        <translation>اعداد الحالة لصانع الميش قد تحتاج اعادة كتابة بناءا على التعديلات التي قمت بها للنموذج

كتابة حالة الميش اولا؟</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdPreferencePage.py" line="310"/>
        <source>Before installing this software, it is advised to run FreeCAD in administrator mode (hold down  the &apos;Shift&apos; key, right-click on the FreeCAD launcher, and choose &apos;Run as administrator&apos;).

If this is not possible, please make sure OpenFOAM is installed in a location to which you have full read/write access rights.

You are not currently running as administrator - do you wish to continue anyway?</source>
		<translation>قبل تثبيت هذه البرمجيات, ينصح بتشغيل FreeCAD في وضع المشرف (اضغط مع الاستمرار على مفتاح&apos;Shift&apos;, انقر زر الماوس الايمن على مشغل FreeCAD, و اختار &apos;التشغيل كمشرف&apos;).

اذا كان ذلك غير ممكن, رجاءا تاكد ان OpenFOAM مثبت في موقع لديك صلاحيات القراءة/الكتابة فيه.

انت حاليا لا تشغل كمشرف - هل تريد ان تستمر على اي حال؟</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/TaskPanelCfdMeshRefinement.py" line="186"/>
        <source>Mesh object not found - please re-create.</source>
		<translation>لم يجد الميش - رجاءا اعد صنعها</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/TaskPanelCfdMeshRefinement.py" line="186"/>
        <source>Missing mesh object</source>
		<translation>الميش مفقودة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/TaskPanelCfdSolverControl.py" line="161"/>
        <source>The case may need to be re-meshed and the case setup re-written based on changes you have made to the model.

Re-mesh and re-write case setup first?</source>
        <translation>قد تحتاج الحالة الى اعادة صناعة الميش و اعادة كتابة اعدادات الحالة بناءا على التعديلات التي قمت بها في النموذج

هل ترغب اولا في اعادة صناعة الميش و اعادة كتابة اعدادات الحالة؟</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/TaskPanelCfdSolverControl.py" line="167"/>
        <source>The case setup may need to be re-written based on changes you have made to the model.

Re-write case setup first?</source>
        <translation>قد تحتاج اعدادات الحالة الى اعادة كتابة بناءا على التغييرات التي قمت بها في النموذج.

هل ترغب اولا في اعادة كتابة الحالة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/TaskPanelCfdSolverControl.py" line="175"/>
        <source>The case may need to be re-meshed based on changes you have made to the model.

Re-mesh case first?</source>
        <translation>قد تحتاج الميش الى اعادة صناعة بناءا على التغييرات التي قمت بها في النموذج.

هل ترغب اولا في اعادة صناعة الميش</translation>
    </message>
</context>
<context>
    <name>FilePicker</name>
    <message>
        <location filename="../CfdOF/CfdPreferencePage.py" line="244"/>
        <source>Choose OpenFOAM directory</source>
        <translation>اختار مجلد OpenFOAM</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdPreferencePage.py" line="253"/>
        <source>Choose ParaView executable</source>
        <translation>اختار برنامج ParaView القابل للتشغيل</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdPreferencePage.py" line="264"/>
        <source>Choose gmsh executable</source>
        <translation>اختار برنامج gmsh القابل للتشغيل</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdPreferencePage.py" line="277"/>
        <source>Choose output directory</source>
		<translation>اختار مجلد الاخراج</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdPreferencePage.py" line="325"/>
        <source>Choose OpenFOAM install file</source>
        <translation>اختلر ملف تثبيت OpenFOAM</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdPreferencePage.py" line="338"/>
        <source>Choose ParaView install file</source>
        <translation>اختلر ملف تثبيت ParaView</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdPreferencePage.py" line="361"/>
        <source>Choose cfMesh archive</source>
        <translation>اختار ارشيف cfMesh</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdPreferencePage.py" line="384"/>
        <source>Choose HiSA archive</source>
        <translation>اختار ارشيف HiSA</translation>
    </message>
</context>
<context>
    <name>Subnames</name>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="58"/>
        <source>No-slip (viscous)</source>
        <translation>عدم الانزلاق (لزج) / No-slip (viscous)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="59"/>
        <source>Slip (inviscid)</source>
        <translation>انزلاق (غير لزج) / Slip (inviscid)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="60"/>
        <source>Partial slip</source>
        <translation>انزلاق جزئي / Partial slip</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="61"/>
        <source>Rotating</source>
        <translation>دوار</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="62"/>
        <source>Translating</source>
		<translation>متحرك</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="63"/>
        <source>Rough</source>
		<translation>خشن</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="65"/>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="73"/>
        <source>Uniform velocity</source>
		<translation>سرعة موحدة</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="66"/>
        <source>Volumetric flow rate</source>
		<translation>معدل تدفق حجمي</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="67"/>
        <source>Mass flow rate</source>
		<translation>معدل تدفق كتلي</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="68"/>
        <source>Total pressure</source>
		<translation>الضغط الكلي</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="69"/>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="72"/>
        <source>Static pressure</source>
		<translation>ضغط ثابت</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="74"/>
        <source>Extrapolated</source>
        <translation>استقراء / Extrapolated</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="76"/>
        <source>Ambient pressure</source>
		<translation>الضغط الجوي</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="76"/>
        <source>Far-field</source>
		<translation>المدى البعيد</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="77"/>
        <source>Symmetry</source>
		<translation>متماثل</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="77"/>
        <source>Periodic</source>
		<translation>دوري</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="78"/>
        <source>Porous Baffle</source>
		<translation>حاجز مسامي</translation>
    </message>
</context>
<context>
    <name>Subtypes</name>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="100"/>
        <source>Zero velocity relative to wall</source>
		<translation>سرعة صفرية مقارنة بالجدار</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="101"/>
        <source>Frictionless wall; zero normal velocity</source>
		<translation>جدار بدون احتكاك: سرعة عادية صفرية</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="102"/>
        <source>Blended fixed/slip</source>
		<translation>ثابت و انزلاق</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="103"/>
        <source>Fixed velocity corresponding to rotation about an axis</source>
		<translation>سرعة ثابتة مقبلة للدوران حول محور</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="104"/>
        <source>Fixed velocity tangential to wall; zero normal velocity</source>
		<translation>سرعة ثابتة مماسة للجدار: سرعة مقابلة صفرية</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="105"/>
        <source>Wall roughness function</source>
		<translation>دالة خشونة الجدار</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="106"/>
        <source>Velocity specified; normal component imposed for reverse flow</source>
		<translation>سرعة محددة: المكون المقابل مفروض للتدفق العكسي</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="107"/>
        <source>Uniform volume flow rate specified</source>
		<translation>معدل تدفق حجمي موحد محدد</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="108"/>
        <source>Uniform mass flow rate specified</source>
		<translation>معدل تدفق كتلي موحد محدد</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="111"/>
        <source>Total pressure specified; treated as static pressure for reverse flow</source>
		<translation>الضغط الكلي المحدد: تعامل كضغط ثابت للتدفق العكسي</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="112"/>
        <source>Static pressure specified</source>
		<translation>ضغط ثابت محدد</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="117"/>
        <source>Static pressure specified for outflow and total pressure for reverse flow</source>
		<translation>ضغط ثابت محدد للتدفق الخارج و مجموع الضغط للتدفق العكسي</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="120"/>
        <source>Normal component imposed for outflow; velocity fixed for reverse flow</source>
		<translation>المكون المقابل المفروض للتدفق الخارج: سرعة ثابتة للتدفق العكسي</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="121"/>
        <source>All fields extrapolated; possibly unstable</source>
		<translation>كل الحقول مستقرة: قد يكون غير مستقر</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="124"/>
        <source>Boundary open to surroundings with total pressure specified</source>
		<translation>حد مفتوح للمحيط بمجموع ضغط محدد</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="125"/>
        <source>Characteristic-based non-reflecting boundary</source>
		<translation>حد غير عاكس على اساس الخصائص</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="128"/>
        <source>Symmetry of flow quantities about boundary face</source>
		<translation>تماثل كميات التدفق حول وجه الحد</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="131"/>
        <source>Rotationally or translationally periodic flows between two boundary faces</source>
		<translation>تواترية تدفق دورية او حركية بين وجهين حد</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="133"/>
        <source>Permeable screen</source>
		<translation>شاشة قابلة للاختراق</translation>
    </message>
</context>
<context>
    <name>TaskPanelCfdDynamicMeshInterfaceRefinement</name>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshInterfaceRefinement.ui" line="14"/>
        <source>Dynamic Mesh</source>
		<translation>الميش الديناميكية</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshInterfaceRefinement.ui" line="35"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Write refinement cell level scalar at each solver write iteration&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
		<translation>اكتب عداد تصغير الخلية كل تكرار كتابة للمحلل</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshInterfaceRefinement.ui" line="38"/>
        <source>Output refinement level field</source>
		<translation>اكتب حقل مستوى التصغير</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshInterfaceRefinement.ui" line="69"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Iteration interval at which to perform dynamic mesh refinement&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
		<translation>فترات التكرار التي ينفذ فيها التصغير الديناميكي للميش</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshInterfaceRefinement.ui" line="91"/>
        <source>Refinement interval</source>
		<translation>فترة التصغير</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshInterfaceRefinement.ui" line="98"/>
        <source>Max refinement level</source>
		<translation>اقصى مستوى تصغير</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshInterfaceRefinement.ui" line="105"/>
        <source>Refine interface of</source>
		<translation>تصغير واجهة </translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshInterfaceRefinement.ui" line="115"/>
        <source>Buffer layers</source>
		<translation>طبقات الحاجز</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshInterfaceRefinement.ui" line="122"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Maximum number of levels of refinement to apply&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
		<translation>اقصى عدد مستويات تصغير لتطبيقها</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshInterfaceRefinement.ui" line="141"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Number of cells layers between refinement and existing cells&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
		<translation>عدد طبقات الخلايا بين التصغير و الخلايا الموجودة مسبقا</translation>
    </message>
</context>
<context>
    <name>TaskPanelCfdDynamicMeshRefinement</name>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshShockRefinement.ui" line="14"/>
        <source>Dynamic Mesh</source>
		<translation>الميش الديناميكية</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshShockRefinement.ui" line="35"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Write refinement cell level scalar at each solver write iteration&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
		<translation>اكتب عداد مستوى التصغير الخلية في كل تكرار كتابة للمحلل</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshShockRefinement.ui" line="38"/>
        <source>Output refinement field</source>
		<translation>اكتب حقل التصغير</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshShockRefinement.ui" line="69"/>
        <source>Refinement interval</source>
		<translation>فترات التصغير</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshShockRefinement.ui" line="76"/>
        <source>Buffer layers</source>
		<translation>طبقات الحاجز</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshShockRefinement.ui" line="83"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Number of cells layers between refinement and existing cells&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
		<translation>عدد طبقات الخلايا بين التصغير و الخلايا الموجودة مسبقا</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshShockRefinement.ui" line="96"/>
        <source>Typically the far-field or input velocity (direction only)</source>
		<translation>عادة يكون الحقل البعيد او سرعة الادخال (الاتجاه فقط)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshShockRefinement.ui" line="99"/>
        <source>Reference velocity direction</source>
		<translation>اتجاه السرعة المرجعي</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshShockRefinement.ui" line="106"/>
        <source>Relative element size</source>
		<translation>حجم العنصر النسبي</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshShockRefinement.ui" line="113"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Maximum number of levels of refinement to apply&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
		<translation>اقصى عدد مستويات لتطبيقها</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshShockRefinement.ui" line="132"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Iteration interval at which to perform dynamic mesh refinement&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
		<translation>فترات التكرار التي ينفذ فيها التصغير الديناميكي للميش</translation>
    </message>
</context>
<context>
    <name>TaskPanelCfdFluidBoundary</name>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="14"/>
        <source>CFD boundary condition</source>
		<translation>حالة حد CFD</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="62"/>
        <source>Boundary </source>
		<translation>حد</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="85"/>
        <source>Sub-type</source>
		<translation>النوع الفرعي</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="102"/>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="681"/>
        <source>Description </source>
		<translation>الوصف</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="112"/>
        <source>Help text</source>
		<translation>نص المساعدة</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="130"/>
        <source>Boundary face list</source>
		<translation>قائمة اوجه الحدود</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="188"/>
        <source>Turbulence specification</source>
		<translation>مواصفات الاضطراب</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="235"/>
        <source>Turbulent kinetic energy (k)</source>
		<translation>طاقة الاضطراب الحركية (k)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="270"/>
        <source>Dissipation rate (ε)</source>
		<translation>معدل التشتت (ε)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="305"/>
        <source>Specific dissipation rate (ω)</source>
		<translation>معدل التشتت المحدد (ω)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="340"/>
        <source>Turbulence intensity (I)</source>
        <translation>شدة الاضطراب (I)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="427"/>
        <source>Length scale (l)</source>
        <translation>مقياس الطول (l)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="462"/>
        <source>Modified turbulent viscosity (ṽ)</source>
        <translation>اللزوجة المضطربة المعدلة (ṽ)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="497"/>
        <source>Intermittency (γ)</source>
        <translation>التقطع (γ)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="532"/>
        <source>Momentum Thickness (Reθ)</source>
        <translation>سمك الزخم (Reθ)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="567"/>
        <source>Turbulent viscosity (v)</source>
        <translation>اللزوجة المضطربة (v)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="625"/>
        <source>Thermal</source>
		<translation>حراري</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="691"/>
        <source>Heat flux</source>
		<translation>تدفق الحرارة</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="704"/>
        <source>Type</source>
		<translation>النوع</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="736"/>
        <source>Temperature</source>
		<translation>الحرارة</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="771"/>
        <source>Heat transfer coefficient</source>
		<translation>معامل انتقال الحرارة</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="825"/>
        <source>Velocity</source>
		<translation>السرعة</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="846"/>
        <source>Car&amp;tesian components</source>
		<translation>المكون الديكارتي</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="853"/>
        <source>Ma&amp;gnitude and normal</source>
		<translation>القيمة المطلقة و مقابل</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="988"/>
        <source>Magnitude</source>
		<translation>القيمة المطلقة </translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1023"/>
        <source>Normal to face</source>
		<translation>مقابل لوجه</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1051"/>
        <source>Pick</source>
		<translation>اختار</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1075"/>
        <source>Inward normal</source>
		<translation>عكس المقابل</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1109"/>
        <source>Pressure</source>
		<translation>ضغط</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1165"/>
        <source>Slip ratio (0.0 - 1.0)</source>
		<translation>معدل الانزلاق (0.0 - 1.0)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1227"/>
        <source>Volume flow rate</source>
		<translation>معدل تدفق حجمي</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1283"/>
        <source>Mass flow rate</source>
		<translation>معدل تدفق كتلي</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1342"/>
        <source>Porous resistance:</source>
		<translation>المقاومة المسامية</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1349"/>
        <source>Pressure &amp;loss coefficient</source>
		<translation>معامل انخفاض الضغط</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1359"/>
        <source>Wire screen parameters</source>
		<translation>ابعاد الشاشة السلكية</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1394"/>
        <source>Pressure loss coefficient</source>
		<translation>معامل انخفاض الضغط</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1448"/>
        <source>Wire diameter</source>
        <translation>قطر السلك</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1483"/>
        <source>Spacing</source>
		<translation>التباعد</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1549"/>
        <source>Roughness height (Ks)</source>
        <translation>ارتفاع الخشونة (Ks)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1578"/>
        <source>Roughness constant (Cs)</source>
        <translation>ثابت الخشونة (Cs)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1634"/>
        <source>Relative to rotating frame</source>
		<translation>بالنسبة للاطار الدوار</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1665"/>
        <source>Rotation axis</source>
		<translation>محور الدوران</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1672"/>
        <source>Rotation origin</source>
		<translation>مركز الدوران</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1679"/>
        <source>Angular velocity</source>
		<translation>السرعة الدورانية</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1682"/>
        <source>Slave patch</source>
		<translation>الحد العبد</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1692"/>
        <source>Master patch</source>
		<translation>الحد السيد</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1708"/>
        <source>Periodic</source>
		<translation>دوري</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1742"/>
        <source>Partner patch</source>
		<translation>الحد الشريك</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1773"/>
        <source>Translational</source>
		<translation>حركية</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1783"/>
        <source>Rotational</source>
		<translation>دورانية</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1817"/>
        <source>Centre of rotation</source>
		<translation>مركز الدوران</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1824"/>
        <source>Rotational axis</source>
		<translation>محور الدوران</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="2008"/>
        <source>Separation vector</source>
		<translation>المتجه الفاصل</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="2108"/>
        <source>Fluid</source>
		<translation>مائع</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="2115"/>
        <source>The proportion of each computational cell composed of the fluid selected.</source>
		<translation>نسبة كل خلية حسابية مكونة من المائع المختار</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="2118"/>
        <source>Volume fraction</source>
		<translation>جزء الحجم</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="2156"/>
        <source>Inflow Volume Fractions</source>
		<translation>جزء الحجم للتدفق الداخل</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="2166"/>
        <source>Use as default boundary condition for unselected faces</source>
		<translation>استخدم كشرط حد افتراضي للوجوه غير المختارة</translation>
    </message>
</context>
<context>
    <name>TaskPanelCfdFluidProperties</name>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidProperties.ui" line="14"/>
        <location filename="../Gui/TaskPanelCfdFluidProperties.ui" line="42"/>
        <source>Fluid properties</source>
		<translation>خصائص المائع</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidProperties.ui" line="29"/>
        <source>Compressible</source>
		<translation>قابل للانضغاط</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidProperties.ui" line="130"/>
        <source>Material name</source>
		<translation>اسم المادة</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidProperties.ui" line="149"/>
        <source>Material Description</source>
		<translation>وصف المادة</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidProperties.ui" line="166"/>
        <source>Predefined fluid library</source>
		<translation>مكتبة المائع المحددة مسبقا</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidProperties.ui" line="176"/>
        <source>Save...</source>
		<translation>حفظ...</translation>
    </message>
</context>
<context>
    <name>TaskPanelCfdInitialiseInternalField</name>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="14"/>
        <source>Initialise flow field</source>
		<translation>تهيئة حقل التدفق</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="35"/>
        <source>Turbulence</source>
		<translation>الاضطراب</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="45"/>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="659"/>
        <source>Use values from boundary</source>
		<translation>استخدم القيم من الحد</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="310"/>
        <source>Reθ</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="510"/>
        <source>Temperature:</source>
		<translation>الحرارة</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="536"/>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="837"/>
        <source>Use value from boundary</source>
		<translation>استخدم القيمة من الحد</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="573"/>
        <source>Thermal</source>
		<translation>حراري</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="601"/>
        <source>Volume Fractions</source>
		<translation>جزء حجمي</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="608"/>
        <source>Fluid</source>
        <translation>مائع</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="615"/>
        <source>The proportion of each computational cell composed of the fluid selected.</source>
		<translation>نسبة كل خلية حسابية مكونة من المائع المختار</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="618"/>
        <source>Volume fraction</source>
		<translation>جزء حجمي</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="768"/>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="823"/>
        <source>Potential flow</source>
		<translation>التدفق المحتمل</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="775"/>
        <source>Specify values</source>
		<translation>حدد القيم</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="788"/>
        <source>Velocity</source>
		<translation>السرعة</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="816"/>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="865"/>
        <source>Pressure</source>
		<translation>الضغط</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="830"/>
        <source>Specify value</source>
		<translation>حدد القيمة</translation>
    </message>
</context>
<context>
    <name>TaskPanelCfdListOfFaces</name>
    <message>
        <location filename="../Gui/TaskPanelCfdListOfFaces.ui" line="14"/>
        <source>Select Faces</source>
		<translation>حدد الوجوه</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdListOfFaces.ui" line="36"/>
        <source>Select in model</source>
		<translation>اختار النموذج</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdListOfFaces.ui" line="83"/>
        <source>So&amp;lid</source>
		<translation>صلب</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdListOfFaces.ui" line="90"/>
        <source>Face, Ed&amp;ge, Vertex</source>
		<translation>وجه, حافة, نقطة</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdListOfFaces.ui" line="100"/>
        <source>Remove</source>
		<translation>حذف</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdListOfFaces.ui" line="107"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Selection&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
		<translation>اختيار</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdListOfFaces.ui" line="114"/>
        <source>Add</source>
		<translation>اضافة</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdListOfFaces.ui" line="122"/>
        <source>Select from list</source>
		<translation>اختار من القائمة</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdListOfFaces.ui" line="131"/>
        <source>Select objects</source>
		<translation>اختار شيئ</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdListOfFaces.ui" line="147"/>
        <source>Select all</source>
		<translation>اختار الكل</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdListOfFaces.ui" line="154"/>
        <source>Select none</source>
		<translation>لا تختار شيئ</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdListOfFaces.ui" line="194"/>
        <source>▼ Select components</source>
		<translation>اختار مكون</translation>
    </message>
</context>
<context>
    <name>TaskPanelCfdMesh</name>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="14"/>
        <source>CFD Mesh</source>
		<translation>ميش CFD</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="46"/>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="59"/>
        <source>Mesh Parameters</source>
		<translation>اعدادات الميش</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="66"/>
        <source>Mesh utility:</source>
		<translation>اداة الميش</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="73"/>
        <source>Base element size:</source>
		<translation>حجم العنصر الاساسي</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="138"/>
        <source>Search</source>
		<translation>بحث</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="244"/>
        <source>Point in mesh</source>
		<translation>نقطة في الميش</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="275"/>
        <source>Edge detection</source>
		<translation>كشف الحافة</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="282"/>
        <source>Implicit</source>
		<translation>ضمني</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="289"/>
        <source>Explicit</source>
		<translation>صريح</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="322"/>
        <source>No of cells between levels</source>
		<translation>عدد الخلايا بين المستويات</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="329"/>
        <source>Relative edge refinement</source>
		<translation>تصغير الحواف النسبية</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="359"/>
        <source>Stop</source>
		<translation>توقف</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="366"/>
        <source>Run mesher</source>
		<translation>شغل صانع الميش</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="379"/>
        <source>Meshing</source>
		<translation>يصنع الميش</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="386"/>
        <source>Write mesh case</source>
		<translation>اكتب حالة الميش</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="393"/>
        <source>Edit</source>
		<translation>عدل</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="422"/>
        <source>Clear</source>
		<translation>نظف</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="429"/>
        <source> Load surface mesh</source>
		<translation>حمل سطح الميش</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="442"/>
        <source>Visualisation</source>
		<translation>التصور</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="456"/>
        <source>Check Mesh</source>
		<translation>فحص الميش</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="482"/>
        <source>Status</source>
		<translation>حالة</translation>
    </message>
</context>
<context>
    <name>TaskPanelCfdMeshRefinement</name>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="14"/>
        <source>Mesh refinement</source>
		<translation>تصغير الميش</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="35"/>
        <source>Volume refinement</source>
		<translation>التصغير الحجمي</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="42"/>
        <source>Surface refinement</source>
		<translation>التصغير السطحي</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="52"/>
        <source>Extrusion</source>
		<translation>بثق</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="83"/>
        <source>Relative element size</source>
		<translation>حجم العنصر النسبي</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="124"/>
        <source>Refinement thickness</source>
		<translation>سمك التصغير</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="131"/>
        <source>Boundary layers</source>
		<translation>طبقات الحد</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="200"/>
        <source>Expansion ratio:</source>
		<translation>معدل التمدد</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="224"/>
        <source>Number of layers:</source>
		<translation>عدد الطبقات</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="242"/>
        <source>Max first cell height (optional):</source>
		<translation>اقصى ارتفاع لاول خلية (اختياري):</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="386"/>
        <source>Edge refinement level</source>
		<translation>مستوى تصغير الحواف</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="414"/>
        <source>Extrusion type</source>
		<translation>نوع البثق</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="424"/>
        <source>Keep existing mesh</source>
		<translation>اترك الميش الموجودة</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="431"/>
        <source>Thickness</source>
		<translation>السمك</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="451"/>
        <source>Angle</source>
		<translation>الزاوية</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="471"/>
        <source>Number of layers</source>
		<translation>عدد الطبقات</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="488"/>
        <source>Expansion ratio</source>
		<translation>نسبة التمدد</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="578"/>
        <source>Axis point</source>
		<translation>نقطة المحور</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="598"/>
        <source>Copy from selected edge</source>
		<translation>انسخ من الحافة المختارة</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="605"/>
        <source>Axis direction</source>
		<translation>اتجاه المحور</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="700"/>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="756"/>
        <source>References</source>
		<translation>المراجع</translation>
    </message>
</context>
<context>
    <name>TaskPanelCfdReportingFunctions</name>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="14"/>
        <source>CFD reporting function</source>
		<translation>دالة تقرير CFD</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="55"/>
        <source>Reporting function</source>
		<translation>دالة تقرير</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="72"/>
        <source>Description </source>
		<translation>الوصف</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="82"/>
        <source>Help text</source>
		<translation>نص المساعدة</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="131"/>
        <source>Parameters</source>
		<translation>اعدادات</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="236"/>
        <source>Centre of rotation</source>
		<translation>مركز الدوران</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="249"/>
        <source>Write fields</source>
		<translation>اكتب الحقول</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="284"/>
        <source>Relative pressure reference</source>
		<translation>الضغط النسبي المرجعي</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="314"/>
        <source>Coefficients</source>
		<translation>المعاملات</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="335"/>
        <source>Lift Direction</source>
		<translation>اتجاه الرفع</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="526"/>
        <source>Free-stream flow speed</source>
		<translation>سرعة التدفق الحر</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="533"/>
        <source>Reference length</source>
		<translation>الطول المرجعي</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="540"/>
        <source>Reference area</source>
		<translation>المساحة المرجعي</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="603"/>
        <source>Drag Direction</source>
		<translation>اتجاه الجر</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="610"/>
        <source>Free-stream density</source>
		<translation>كثافة التدفق الحر</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="665"/>
        <source>Patch list</source>
		<translation>قائمة الحدود</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="683"/>
        <source>Patches                          </source>
		<translation>الحدود</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="716"/>
        <source>Spatial data binning</source>
		<translation>تثبيت البيانات المكانية</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="737"/>
        <source>Number of bins</source>
		<translation>عدد النقات المثبتة</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="831"/>
        <source>Binning direction</source>
        <translation>اتجاه التثبيت</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="844"/>
        <source>Cumulative</source>
        <translation>التراكمي</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="911"/>
        <source>Sample field name</source>
		<translation>اسم الحقل العينة</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="997"/>
        <source>Probe location (x, y, z)</source>
        <translation>موقع المجس (x, y, z)</translation>
    </message>
</context>
<context>
    <name>TaskPanelCfdScalarTransportFunctions</name>
    <message>
        <location filename="../Gui/TaskPanelCfdScalarTransportFunctions.ui" line="14"/>
        <source>Scalar transport function</source>
		<translation>دالة النقل العددي </translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdScalarTransportFunctions.ui" line="52"/>
        <source>Scalar Transport</source>
        <translation>النقل العددي</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdScalarTransportFunctions.ui" line="70"/>
        <source>Viscous/turbulent</source>
		<translation>لزج/مضطرب</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdScalarTransportFunctions.ui" line="77"/>
        <source>Scalar field name</source>
        <translation>اسم الحقل العددي</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdScalarTransportFunctions.ui" line="84"/>
        <source>Specified coefficient</source>
		<translation>المعامل المحدد</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdScalarTransportFunctions.ui" line="135"/>
        <source>Restrict to phase</source>
		<translation>قيد بالطور</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdScalarTransportFunctions.ui" line="145"/>
        <source>Diffusivity</source>
		<translation>التشتت</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdScalarTransportFunctions.ui" line="160"/>
        <source>Scalar injection</source>
		<translation>الحقن العددي</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdScalarTransportFunctions.ui" line="269"/>
        <source>Injection point (x, y, z)</source>
        <translation>نقطة الحقن (x, y, z)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdScalarTransportFunctions.ui" line="282"/>
        <source>Injection rate</source>
		<translation>معدل الحقن</translation>
    </message>
</context>
<context>
    <name>TaskPanelCfdSolverControl</name>
    <message>
        <location filename="../Gui/TaskPanelCfdSolverControl.ui" line="14"/>
        <source>Analysis control</source>
		<translation>التحكم في التحليل</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdSolverControl.ui" line="40"/>
        <source>Write</source>
		<translation>اكتب</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdSolverControl.ui" line="50"/>
        <source>Edit</source>
		<translation>عدل</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdSolverControl.ui" line="63"/>
        <source>Case setup</source>
		<translation>اعداد الحالة</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdSolverControl.ui" line="95"/>
        <source>Stop</source>
		<translation>ايقاف</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdSolverControl.ui" line="105"/>
        <source>Run</source>
		<translation>تشغيل</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdSolverControl.ui" line="118"/>
        <source>Solver</source>
		<translation>المحلل</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdSolverControl.ui" line="176"/>
        <source>Results</source>
		<translation>النتائج</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdSolverControl.ui" line="199"/>
        <source>Status</source>
		<translation>الوضع</translation>
    </message>
</context>
<context>
    <name>TaskPanelCfdZone</name>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="14"/>
        <source>CFD Zone</source>
		<translation>منطقة CFD</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="55"/>
        <source>Correspond to directions in which the velocity is scaled but not rotated by the porous medium</source>
		<translation>موافق للاتجاه الذي تكون فيه السرعة مقياسية و ليست دائرية</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="58"/>
        <source>Principal directions</source>
		<translation>الاتجاه الرئيسي</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="152"/>
        <source>Porous drag coefficients in principal directions</source>
		<translation>معامل سحب المنطقة المسامية في الاتجاه الرئيسي</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="396"/>
        <source>Viscous (d)</source>
        <translation>اللزوجة(d)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="434"/>
        <source>Inertial (f)</source>
        <translation>القصور الذاتي (f)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="546"/>
        <source>Porous correlation</source>
		<translation>الارتباط المسامي</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="565"/>
        <source>Tube outer diameter</source>
		<translation>القطر الخارجي للانبوب</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="594"/>
        <source>Longitudinal axis of the tube</source>
		<translation>المحور الطولي للانبوب</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="597"/>
        <source>Tube axis</source>
		<translation>محور الانبوب</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="685"/>
        <source>Spacing between tubes normal to layers</source>
		<translation>المسافة بين الانابيب مقابل الطبقات</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="688"/>
        <source>Tube spacing</source>
		<translation>تباعد الانابيب</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="720"/>
        <source>Direction of spacing normal to layers</source>
		<translation>اتجاه التباعد مقابل الطبقات</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="723"/>
        <source>Spacing direction</source>
		<translation>اتجاه التباعد</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="793"/>
        <source>Multiplier used to obtain spacing perpendicular to spacing direction</source>
		<translation>المضاعف المستخدم للحصول على التباعد القائم على اتجاه التباعد</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="796"/>
        <source>Spacing aspect ratio</source>
		<translation>نسبة العرض الى الارتفاع للتباعد</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="852"/>
        <source>Estimated incident (superficial) velocity used for Reynolds number adjustment of correlation.</source>
		<translation>سرعة الحادث المقدرة (سطحي) المستخدمة لتعديل ارتباط رقم رينولدز </translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="855"/>
        <source>Velocity estimate</source>
		<translation>تقدير السرعة</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="899"/>
        <source>Set velocity</source>
		<translation>ضبط السرعة</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="936"/>
        <source>Set volume fractions</source>
		<translation>ضبط جزء الحجم</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="1044"/>
        <source>Set pressure</source>
		<translation>ضبط الضغط</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="1072"/>
        <source>Set temperature</source>
		<translation>ضبط الحرارة</translation>
    </message>
</context>
<context>
    <name>TaskPanelPhysics</name>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="14"/>
        <source>Select physics model</source>
		<translation>اختر النموذج الفيزيائي</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="44"/>
        <source>Stead&amp;y</source>
		<translation>ثابت</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="57"/>
        <source>&amp;Transient</source>
		<translation>متحرك</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="70"/>
        <source>Time</source>
		<translation>الزمن</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="170"/>
        <source>Moving reference frame (SRF)</source>
        <translation>الاطار المرجعي المتحرك (SRF)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="177"/>
        <source>RPM</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="184"/>
        <source>Rotational axis</source>
		<translation>محور الدوران</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="213"/>
        <source>Centre of rotation</source>
		<translation>مركز الدوران</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="313"/>
        <source>Flow</source>
		<translation>التدفق</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="347"/>
        <source>Isothermal</source>
		<translation>بدون حرارة</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="360"/>
        <source>High Mach number</source>
		<translation>رقم ماخ عالي</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="370"/>
        <source>Rotating frame (SRF)</source>
        <translation>اطار دوار (SRF)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="404"/>
        <source>Single phase</source>
		<translation>طور واحد</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="417"/>
        <source>Multiphase - free surface</source>
		<translation>متعدد الاطوار - سطح حر</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="430"/>
        <source>Viscous</source>
		<translation>لزج</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="492"/>
        <source>&amp;Laminar</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="499"/>
        <source>Detached Eddy Simulation</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="509"/>
        <source>Reynolds Averaged Navier-Stokes</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="519"/>
        <source>Large Eddy Simulation</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="550"/>
        <source>Model</source>
		<translation>النموذج</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="589"/>
        <source>Turbulence</source>
		<translation>الاضطراب</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="695"/>
        <source>Gravity</source>
		<translation>الجاذبية</translation>
    </message>
</context>
<context>
    <name>Workbench</name>
    <message>
        <location filename="../InitGui.py" line="44"/>
        <location filename="../InitGui.py" line="112"/>
        <location filename="../InitGui.py" line="120"/>
        <source>CfdOF</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../InitGui.py" line="46"/>
        <source>CfdOF workbench</source>
        <translation>طاولة عمل CfdOF</translation>
    </message>
    <message>
        <location filename="../InitGui.py" line="96"/>
        <source>Dynamic mesh refinement</source>
		<translation>التصغير الديناميكي للميش</translation>
    </message>
    <message>
        <location filename="../InitGui.py" line="105"/>
        <source>Development</source>
		<translation>التطور</translation>
    </message>
    <message>
        <location filename="../InitGui.py" line="115"/>
        <location filename="../InitGui.py" line="117"/>
        <location filename="../InitGui.py" line="119"/>
        <source>&amp;CfdOF</source>
        <translation type="unfinished"></translation>
    </message>
</context>
</TS>
