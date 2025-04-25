<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1">
<context>
    <name>App::Property</name>
    <message>
        <location filename="../CfdOF/CfdAnalysis.py" line="68"/>
        <source>Path to which cases are written (blank to use system default; relative path is relative to location of current file)</source>
        <translation>caseが書き込まれるパス (空白の場合はシステムデフォルト, 相対パスの場合は現在のファイルの場所が基準になります)</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdAnalysis.py" line="76"/>
        <source>Active analysis object in document</source>
        <translation>ドキュメント内のアクティブな分析オブジェクト</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdAnalysis.py" line="85"/>
        <source>Mesh setup needs to be re-written</source>
        <translation>メッシュ設定を再保存する必要がある</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdAnalysis.py" line="93"/>
        <source>Case setup needs to be re-written</source>
        <translation>ケース設定を再保存する必要がある</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdAnalysis.py" line="101"/>
        <source>Mesher needs to be re-run before running solver</source>
        <translation>ソルバーを実行する前にメッシャーを再実行する必要がある</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdAnalysis.py" line="109"/>
        <source>Use a hostfile for parallel cluster runs</source>
        <translation>並列クラスタ実行にホストファイルを使用する</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdAnalysis.py" line="117"/>
        <source>Hostfile name</source>
        <translation>ホストファイル名</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="104"/>
        <source>Name of directory in which the mesh is created</source>
        <translation>メッシュが作成されるディレクトリ名</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="117"/>
        <source>Maximum relative linear deflection for built-in surface triangulation</source>
        <translation>サーフェス三角メッシュ生成時の最大相対変位</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="127"/>
        <source>Mesh elements per 360 degrees for surface triangulation with GMSH</source>
        <translation>GMSHを使用したサーフェス三角メッシュにおける360度あたりのメッシュ要素数</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="139"/>
        <source>Number of parallel processes (only applicable to cfMesh and snappyHexMesh)</source>
        <translation>並列プロセス数 (cfMeshとsnappyHexMeshのみ適用)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="152"/>
        <source>Number of parallel threads per process (only applicable to cfMesh and gmsh).
0 means use all available (if NumberOfProcesses = 1) or use 1 (if NumberOfProcesses &gt; 1)</source>
        <translation>cfMesh/gmsh用: プロセスあたりの並列スレッド数 (0が設定された場合は, NumberOfProcesses = 1ならば使用可能な全てのスレッドを使い, NumberOfProcesses &gt; 1ならば各プロセスで1スレッドを使う)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="161"/>
        <source>Part object to mesh</source>
        <translation>メッシュするPartオブジェクト</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="170"/>
        <source>Meshing utilities</source>
        <translation>メッシュユーティリティ</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="181"/>
        <source>Max mesh element size (0.0 = infinity)</source>
        <translation>メッシュ要素サイズの最大値 (0.0ならば無限大)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="193"/>
        <source>Location vector inside the region to be meshed (must not coincide with a cell face)</source>
        <translation>メッシュ対象領域内の位置ベクトル (セル面と一致しないこと)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="202"/>
        <source>Number of cells between each level of refinement</source>
        <translation>細分化各レベル間のセル数</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="211"/>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="186"/>
        <source>Relative edge (feature) refinement</source>
        <translation>相対エッジ細分化</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="221"/>
        <source>Convert to polyhedral dual mesh</source>
        <translation>ポリへドラルデュアルメッシュに変換</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="231"/>
        <source>Use implicit edge detection</source>
        <translation>暗黙的なエッジ検出を使用</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="241"/>
        <source>Dimension of mesh elements (Default 3D)</source>
        <translation>メッシュ要素の次元 (デフォルトは3D)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="202"/>
        <source>Set the target refinement interface phase</source>
        <translation>細分化対象インターフェースの相 (フェーズ) を設定</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="214"/>
        <source>Set the interval at which to run the dynamic mesh refinement</source>
        <translation>動的メッシュ細分化を実行するインターバルを設定</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="223"/>
        <source>Set the maximum dynamic mesh refinement level</source>
        <translation>動的メッシュ細分化レベルの最大値を設定</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="235"/>
        <source>Set the number of buffer layers between refined and existing cells</source>
        <translation>細分化セルと既存セルの間のバッファ層の数を設定</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="247"/>
        <source>Whether to write the dynamic mesh refinement fields after refinement</source>
        <translation>細分化後に動的メッシュ細分化フィールドを書き込む</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="283"/>
        <source>Reference velocity direction (typically free-stream/input value)</source>
        <translation>速度方向の参照値 (通常は自由流/入力値)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="292"/>
        <source>Refinement relative to the base mesh</source>
        <translation>ベースメッシュに対する相対的な細分化</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="304"/>
        <source>Interval at which to run the dynamic mesh refinement in steady analyses</source>
        <translation>定常解析で動的メッシュ細分化を行うインターバル</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="316"/>
        <source>Interval at which to run the dynamic mesh refinement in transient analyses</source>
        <translation>非定常解析で動的メッシュ細分化を行うインターバル</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="328"/>
        <source>Number of buffer layers between refined and existing cells</source>
        <translation>細分化セルと既存セルの間のバッファ層の数</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="340"/>
        <source>Whether to write the indicator fields for shock wave detection</source>
        <translation>衝撃波検出のインジケーターフィールドを書き込む</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="100"/>
        <source>List of mesh refinement objects</source>
        <translation>メッシュ細分化オブジェクトのリスト</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="121"/>
        <source>Whether the refinement region is a volume rather than surface</source>
        <translation>細分化領域はサーフェースではなくボリューム</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="130"/>
        <source>Defines an extrusion from a patch</source>
        <translation>パッチからの押し出しを定義</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="141"/>
        <source>Set relative length of the elements for this region</source>
        <translation>この領域の要素の相対的な長さを設定</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="150"/>
        <source>Set refinement region thickness</source>
        <translation>細分化領域の厚さを設定</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="159"/>
        <source>Set number of boundary layers</source>
        <translation>境界層の数を設定</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="168"/>
        <source>Set expansion ratio within boundary layers</source>
        <translation>境界層内の膨張率を設定</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="177"/>
        <source>Set the maximum first layer height</source>
        <translation>初層の最大高さを設定</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="195"/>
        <source>Type of extrusion</source>
        <translation>押し出しのタイプ</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="207"/>
        <source>If true, then the extrusion extends the existing mesh rather than replacing it</source>
        <translation>押し出しが既存のメッシュを置き換えず拡張する</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="216"/>
        <source>Total distance of the extruded layers</source>
        <translation>押し出しレイヤーの総距離</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="225"/>
        <source>Total angle through which the patch is extruded</source>
        <translation>パッチが押し出される合計角度</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="234"/>
        <source>Number of extrusion layers to add</source>
        <translation>追加する押し出し層の層数</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="243"/>
        <source>Expansion ratio of extrusion layers</source>
        <translation>押出層の膨張比率</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="252"/>
        <source>Point on axis for sector extrusion</source>
        <translation>セクター押し出し軸の基準点</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="261"/>
        <source>Direction of axis for sector extrusion</source>
        <translation>セクター押し出し軸の方向</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="93"/>
        <source>Type of reporting function</source>
        <translation>レポーティングファンクションのタイプ</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="102"/>
        <source>Patch on which to create the function object</source>
        <translation>ファンクションオブジェクトを適用するパッチ</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="112"/>
        <source>Reference density</source>
        <translation>密度の参照値</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="120"/>
        <source>Reference pressure</source>
        <translation>圧力の参照値</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="128"/>
        <source>Centre of rotation</source>
        <translation>回転の基準点</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="136"/>
        <source>Whether to write output fields</source>
        <translation>出力フィールドを書き込む</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="146"/>
        <source>Lift direction (x component)</source>
        <translation>揚力方向</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="155"/>
        <source>Drag direction</source>
        <translation>抗力方向</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="164"/>
        <source>Freestream velocity magnitude</source>
        <translation>自由流速度の大きさ</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="172"/>
        <source>Coefficient length reference</source>
        <translation>係数の長さの参照値</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="180"/>
        <source>Coefficient area reference</source>
        <translation>係数の面積の参照値</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="190"/>
        <source>Number of bins</source>
        <translation>ビンの数</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="198"/>
        <source>Binning direction</source>
        <translation>ビニング方向</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="206"/>
        <source>Cumulative</source>
        <translation>累積値</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="216"/>
        <source>Name of the field to sample</source>
        <translation>サンプリング対象フィールド名</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="225"/>
        <source>Location of the probe sample</source>
        <translation>プローブサンプルの位置</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="324"/>
        <location filename="../CfdOF/Solve/CfdZone.py" line="121"/>
        <source>Boundary faces</source>
        <translation>境界面</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="350"/>
        <source>Boundary condition category</source>
        <translation>境界条件カテゴリー</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="363"/>
        <source>Boundary condition type</source>
        <translation>境界条件タイプ</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="371"/>
        <source>Whether to use components of velocity</source>
        <translation>速度成分を使用する</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="379"/>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="127"/>
        <location filename="../CfdOF/Solve/CfdZone.py" line="281"/>
        <source>Velocity (x component)</source>
        <translation>速度 (x方向)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="387"/>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="135"/>
        <location filename="../CfdOF/Solve/CfdZone.py" line="289"/>
        <source>Velocity (y component)</source>
        <translation>速度 (y方向)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="395"/>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="143"/>
        <location filename="../CfdOF/Solve/CfdZone.py" line="297"/>
        <source>Velocity (z component)</source>
        <translation>速度 (z方向)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="403"/>
        <source>Velocity magnitude</source>
        <translation>ベクトル速度の大きさ</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="411"/>
        <source>Face describing direction (normal)</source>
        <translation>面の向き (法線)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="419"/>
        <source>Direction is inward-pointing if true</source>
        <translation>面が内向き (trueなら内向き)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="427"/>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="151"/>
        <location filename="../CfdOF/Solve/CfdZone.py" line="313"/>
        <source>Static pressure</source>
        <translation>静圧</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="435"/>
        <source>Slip ratio</source>
        <translation>スリップ比率</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="443"/>
        <source>Volume flow rate</source>
        <translation>体積流量</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="451"/>
        <source>Mass flow rate</source>
        <translation>質量流量</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="460"/>
        <source>Relative velocity</source>
        <translation>相対速度</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="469"/>
        <source>Baffle</source>
        <translation>バッフル</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="479"/>
        <source>Porous baffle pressure drop coefficient</source>
        <translation>多孔質バッフルの圧力降下係数</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="487"/>
        <source>Porous screen mesh diameter</source>
        <translation>多孔質スクリーンのメッシュ線径</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="495"/>
        <source>Porous screen mesh spacing</source>
        <translation>多孔質スクリーンのメッシュ間隔</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="504"/>
        <source>Sand-grain roughness</source>
        <translation>砂粒の粗さ / Sand-grain roughness</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="512"/>
        <source>Coefficient of roughness [0.5-1]</source>
        <translation>粗さの係数 [0.5-1] / Coefficient of roughness</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="521"/>
        <source>Type of thermal boundary</source>
        <translation>熱境界のタイプ</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="529"/>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="167"/>
        <location filename="../CfdOF/Solve/CfdZone.py" line="329"/>
        <source>Temperature</source>
        <translation>温度</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="537"/>
        <source>Wall heat flux</source>
        <translation>壁面の熱流束</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="545"/>
        <source>Wall heat transfer coefficient</source>
        <translation>壁面の熱伝達係数</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="555"/>
        <source>Rotational or translational periodicity</source>
        <translation>回転周期または平行移動周期</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="563"/>
        <source>Centre of rotation for rotational periodics</source>
        <translation>回転周期の回転基準点</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="571"/>
        <source>Axis of rotational for rotational periodics</source>
        <translation>回転周期の回転軸の方向</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="579"/>
        <source>Separation vector for translational periodics</source>
        <translation>平行周期の分離ベクトル</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="587"/>
        <source>Partner patch for the slave periodic</source>
        <translation>スレーブ周期のパートナーパッチ</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="597"/>
        <source>Whether the current patch is the master or slave patch</source>
        <translation>現在のパッチ (マスターパッチまたはスレーブパッチ)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="613"/>
        <source>Turbulent quantities specified</source>
        <translation>乱流量の指定</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="624"/>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="183"/>
        <source>Turbulent kinetic energy</source>
        <translation>乱流運動エネルギー</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="632"/>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="191"/>
        <source>Specific turbulent dissipation rate</source>
        <translation>乱流の比散逸率</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="642"/>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="199"/>
        <source>Turbulent dissipation rate</source>
        <translation>乱流の散逸率</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="652"/>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="207"/>
        <source>Modified turbulent viscosity</source>
        <translation>変形乱流粘性</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="662"/>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="215"/>
        <source>Turbulent intermittency</source>
        <translation>乱流の間欠度</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="670"/>
        <source>Transition momentum thickness Reynolds number</source>
        <translation>遷移運動量厚さレイノルズ数</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="680"/>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="688"/>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="696"/>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="231"/>
        <source>Turbulent viscosity</source>
        <translation>乱流粘性</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="706"/>
        <source>Turbulence intensity (percent)</source>
        <translation>乱流強度 (パーセント)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="719"/>
        <source>Length scale of turbulent eddies</source>
        <translation>乱流渦の長さスケール</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="727"/>
        <source>Volume fractions</source>
        <translation>体積分率</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidMaterial.py" line="98"/>
        <source>List of material shapes</source>
        <translation>マテリアルシェイプのリスト</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidMaterial.py" line="108"/>
        <source>Type of material</source>
        <translation>マテリアルの種類</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="95"/>
        <source>Initialise velocity with potential flow solution</source>
        <translation>ポテンシャルフロー解で速度を初期化する</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="103"/>
        <source>Initialise pressure with potential flow solution</source>
        <translation>ポテンシャルフロー解で圧力を初期化する</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="111"/>
        <source>Initialise with flow values from inlet</source>
        <translation>フロー値の初期値を流入口から取得</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="119"/>
        <source>Initialise with flow values from outlet</source>
        <translation>フロー値の初期値を流出口から取得</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="159"/>
        <source>Initialise with temperature value from inlet</source>
        <translation>温度の初期値を流入口から取得</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="175"/>
        <source>Initialise turbulence with values from inlet</source>
        <translation>乱流の初期値を流入口から取得</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="223"/>
        <source>Transition Momentum Thickness Reynolds Number</source>
        <translation>遷移運動量厚さレイノルズ数</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="240"/>
        <location filename="../CfdOF/Solve/CfdZone.py" line="345"/>
        <source>Volume fraction values</source>
        <translation>体積分率</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="248"/>
        <source>U boundary</source>
        <translation>U境界</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="256"/>
        <source>P boundary</source>
        <translation>P境界</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="264"/>
        <source>T boundary</source>
        <translation>T境界</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="272"/>
        <source>Turbulence boundary</source>
        <translation>乱流境界</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdPhysicsSelection.py" line="114"/>
        <source>Resolve time dependence</source>
        <translation>時間依存性の解決方法</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdPhysicsSelection.py" line="130"/>
        <source>Flow algorithm</source>
        <translation>フローアルゴリズム</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdPhysicsSelection.py" line="148"/>
        <source>Type of phases present</source>
        <translation>フェーズのタイプ</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdPhysicsSelection.py" line="158"/>
        <source>Type of turbulence modelling</source>
        <translation>乱流モデリングのタイプ</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdPhysicsSelection.py" line="182"/>
        <source>Turbulence model</source>
        <translation>乱流モデル</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdPhysicsSelection.py" line="193"/>
        <source>Gravitational acceleration vector (x component)</source>
        <translation>重力加速度ベクトル (x成分)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdPhysicsSelection.py" line="201"/>
        <source>Gravitational acceleration vector (y component)</source>
        <translation>重力加速度ベクトル (y成分)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdPhysicsSelection.py" line="209"/>
        <source>Gravitational acceleration vector (z component)</source>
        <translation>重力加速度ベクトル (Z成分)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdPhysicsSelection.py" line="219"/>
        <source>Single Rotating Frame model enabled</source>
        <translation>Single Rotating Frame(SRF)モデルが有効</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdPhysicsSelection.py" line="228"/>
        <source>Rotational speed</source>
        <translation>回転速度</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdPhysicsSelection.py" line="237"/>
        <source>Centre of rotation (SRF)</source>
        <translation>回転の基準点 (SRF)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdPhysicsSelection.py" line="246"/>
        <source>Axis of rotation (SRF)</source>
        <translation>回転軸の方向 (SRF)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdScalarTransportFunction.py" line="85"/>
        <source>Name of the scalar transport field</source>
        <translation>スカラー輸送フィールド名</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdScalarTransportFunction.py" line="96"/>
        <source>Use fixed value for diffusivity rather than viscosity</source>
        <translation>粘度ではなく拡散率に固定値を使用</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdScalarTransportFunction.py" line="106"/>
        <source>Diffusion coefficient for fixed diffusivity</source>
        <translation>固定拡散率の拡散係数</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdScalarTransportFunction.py" line="115"/>
        <source>Restrict transport within phase</source>
        <translation>フェーズ内の輸送を制限</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdScalarTransportFunction.py" line="124"/>
        <source>Transport within phase</source>
        <translation>フェーズ内輸送</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdScalarTransportFunction.py" line="133"/>
        <source>Injection rate</source>
        <translation>インジェクション率</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdScalarTransportFunction.py" line="142"/>
        <source>Location of the injection point</source>
        <translation>インジェクション点の位置</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="96"/>
        <source>Name of case directory where the input files are written</source>
        <translation>caseディレクトリ名 (入力ファイルが保存される)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="104"/>
        <source>Parallel analysis on multiple CPU cores</source>
        <translation>複数のCPUコアによる並列解析</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="112"/>
        <source>Number of cores on which to run parallel analysis</source>
        <translation>並列解析の実行コア数</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="123"/>
        <source>Sets a limit on the number of time directories that are stored by overwriting time directories on a cyclic basis.  Set to 0 to disable</source>
        <translation>周期的に上書き保存されるタイムディレクトリ数の上限 (無効にするには0を設定)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="134"/>
        <source>Maximum number of iterations to run steady-state analysis</source>
        <translation>定常解析の最大反復回数</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="142"/>
        <source>Iteration output interval</source>
        <translation>出力の反復インターバル</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="150"/>
        <source>Global absolute solution convergence criterion</source>
        <translation>グローバル絶対収束判定基準</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="159"/>
        <source>Whether to restart or resume solving</source>
        <translation>解析をリスタートするかレジュームするか</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="168"/>
        <source>Total time to run transient solution</source>
        <translation>非定常解析の総実行時間</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="176"/>
        <source>Time step increment</source>
        <translation>タイムステップ増分</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="184"/>
        <source>Maximum CFL number for transient simulations</source>
        <translation>過渡シミュレーションにおけるCFL数の最大値</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="194"/>
        <source>Maximum free-surface CFL number for transient simulations</source>
        <translation>過渡シミュレーションにおける自由表面CFL数の最大値</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="202"/>
        <source>Output time interval</source>
        <translation>結果出力のインターバル時間</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="141"/>
        <source>Porous drag model</source>
        <translation>多孔質抗力モデル</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="150"/>
        <source>Darcy coefficient (direction 1)</source>
        <translation>ダルシー係数 (方向1)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="158"/>
        <source>Darcy coefficient (direction 2)</source>
        <translation>ダルシー係数 (方向2)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="166"/>
        <source>Darcy coefficient (direction 3)</source>
        <translation>ダルシー係数 (方向3)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="174"/>
        <source>Forchheimer coefficient (direction 1)</source>
        <translation>フォルヒハイマー係数 (方向1)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="182"/>
        <source>Forchheimer coefficient (direction 2)</source>
        <translation>フォルヒハイマー係数 (方向2)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="190"/>
        <source>Forchheimer coefficient (direction 3)</source>
        <translation>フォルヒハイマー係数 (方向3)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="198"/>
        <source>Principal direction 1</source>
        <translation>主要方向1</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="206"/>
        <source>Principal direction 2</source>
        <translation>主要方向2</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="214"/>
        <source>Principal direction 3</source>
        <translation>主要方向3</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="222"/>
        <source>Tube diameter</source>
        <translation>チューブ径</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="230"/>
        <source>Direction parallel to tubes</source>
        <translation>チューブに平行な方向</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="238"/>
        <source>Spacing between tube layers</source>
        <translation>チューブ層間の間隔</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="246"/>
        <source>Direction normal to tube layers</source>
        <translation>チューブ層に垂直な方向</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="256"/>
        <source>Tube spacing aspect ratio (layer-to-layer : tubes in layer)</source>
        <translation>チューブ間隔のアスペクト比 (層間：層内のチューブ数)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="264"/>
        <source>Approximate flow velocity</source>
        <translation>おおよその流速</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="273"/>
        <source>Whether the zone initialises velocity</source>
        <translation>ゾーンが速度を初期化する</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="305"/>
        <source>Whether the zone initialises pressure</source>
        <translation>ゾーンが圧力を初期化する</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="321"/>
        <source>Whether the zone initialises temperature</source>
        <translation>ゾーンが温度条件を初期化する</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="337"/>
        <source>Whether the zone initialises volume fraction</source>
        <translation>ゾーンが体積分率を初期化する</translation>
    </message>
</context>
<context>
    <name>Boundary</name>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="45"/>
        <source>Wall</source>
        <translation>壁面 / Wall</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="46"/>
        <source>Inlet</source>
        <translation>流入 / Inlet</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="47"/>
        <source>Outlet</source>
        <translation>流出 / Outlet</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="48"/>
        <source>Open</source>
        <translation>開口 / Open</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="49"/>
        <source>Constraint</source>
        <translation>拘束 / Constraint</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="50"/>
        <source>Baffle</source>
        <translation>バッフル / Baffle</translation>
    </message>
</context>
<context>
    <name>CfdOF_Analysis</name>
    <message>
        <location filename="../CfdOF/CfdAnalysis.py" line="163"/>
        <source>Analysis container</source>
        <translation>解析コンテナ</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdAnalysis.py" line="167"/>
        <source>Creates an analysis container with a CFD solver</source>
        <translation>CFDソルバーの解析コンテナを作成します</translation>
    </message>
</context>
<context>
    <name>CfdOF_DynamicMeshInterfaceRefinement</name>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="90"/>
        <source>Interface dynamic refinement</source>
        <translation>インターフェースの動的な細分化</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="95"/>
        <source>Activates adaptive mesh refinement at free-surface interfaces</source>
        <translation>自由表面インターフェースの適合格子細分化を有効化します</translation>
    </message>
</context>
<context>
    <name>CfdOF_DynamicMeshShockRefinement</name>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="143"/>
        <source>Shockwave dynamic refinement</source>
        <translation>衝撃波の動的な細分化</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="148"/>
        <source>Activates adaptive mesh refinement for shocks</source>
        <translation>衝撃波のための適合格子細分化を有効化します</translation>
    </message>
</context>
<context>
    <name>CfdOF_FluidBoundary</name>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="296"/>
        <source>Fluid boundary</source>
        <translation>境界条件</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="300"/>
        <source>Creates a CFD fluid boundary</source>
        <translation>CFD境界条件を作成します</translation>
    </message>
</context>
<context>
    <name>CfdOF_FluidMaterial</name>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidMaterial.py" line="54"/>
        <location filename="../CfdOF/Solve/CfdFluidMaterial.py" line="57"/>
        <source>Add fluid properties</source>
        <translation>流体物性の追加</translation>
    </message>
</context>
<context>
    <name>CfdOF_GroupDynamicMeshRefinement</name>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="46"/>
        <source>Dynamic mesh refinement</source>
        <translation>動的なメッシュ細分化</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdDynamicMeshRefinement.py" line="50"/>
        <source>Allows adaptive refinement of the mesh</source>
        <translation>適合格子細分化を可能にします</translation>
    </message>
</context>
<context>
    <name>CfdOF_InitialisationZone</name>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="90"/>
        <source>Initialisation zone</source>
        <translation>初期化ゾーン</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="95"/>
        <source>Select and create an initialisation zone</source>
        <translation>初期化ゾーンを選択および作成します</translation>
    </message>
</context>
<context>
    <name>CfdOF_InitialiseInternal</name>
    <message>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="54"/>
        <source>Initialise</source>
        <translation>初期化</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdInitialiseFlowField.py" line="60"/>
        <source>Initialise internal flow variables based on the selected physics model</source>
        <translation>選択する物理モデルに基づいて内部のフロー変数を初期化します</translation>
    </message>
</context>
<context>
    <name>CfdOF_MeshFromShape</name>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="50"/>
        <source>CFD mesh</source>
        <translation>CFDメッシュ</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMesh.py" line="54"/>
        <source>Create a mesh using cfMesh, snappyHexMesh or gmsh</source>
        <translation>cfMesh/snappyHexMesh/gmshを使用してメッシュ(計算格子)を作成します</translation>
    </message>
</context>
<context>
    <name>CfdOF_MeshRegion</name>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="62"/>
        <source>Mesh refinement</source>
        <translation>メッシュ細分化</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/CfdMeshRefinement.py" line="66"/>
        <source>Creates a mesh refinement</source>
        <translation>メッシュ細分化を作成します</translation>
    </message>
</context>
<context>
    <name>CfdOF_OpenPreferences</name>
    <message>
        <location filename="../CfdOF/CfdOpenPreferencesPage.py" line="33"/>
        <source>Open preferences</source>
        <translation>設定を開く</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdOpenPreferencesPage.py" line="36"/>
        <source>Opens the CfdOF preferences page</source>
        <translation>CfdOFの設定ページを開きます</translation>
    </message>
</context>
<context>
    <name>CfdOF_PhysicsModel</name>
    <message>
        <location filename="../CfdOF/Solve/CfdPhysicsSelection.py" line="54"/>
        <source>Select models</source>
        <translation>モデル選択</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdPhysicsSelection.py" line="58"/>
        <source>Select the physics model</source>
        <translation>物理モデルを選択します</translation>
    </message>
</context>
<context>
    <name>CfdOF_PorousZone</name>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="70"/>
        <source>Porous zone</source>
        <translation>多孔質ゾーン</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdZone.py" line="74"/>
        <source>Select and create a porous zone</source>
        <translation>多孔質ゾーンを選択および作成します</translation>
    </message>
</context>
<context>
    <name>CfdOF_ReloadWorkbench</name>
    <message>
        <location filename="../CfdOF/CfdReloadWorkbench.py" line="37"/>
        <source>Reload CfdOF workbench</source>
        <translation>CfdOFワークベンチの再読み込み</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdReloadWorkbench.py" line="41"/>
        <source>Attempt to reload all CfdOF source files from disk. May break open documents!</source>
        <translation>ディスクからすべてのCfdOFソースファイルの再読み込みを試みます. 開いているドキュメントが破損する可能性があります.</translation>
    </message>
</context>
<context>
    <name>CfdOF_ReportingFunctions</name>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="60"/>
        <source>Reporting function</source>
        <translation>レポーティングファンクション</translation>
    </message>
    <message>
        <location filename="../CfdOF/PostProcess/CfdReportingFunction.py" line="64"/>
        <source>Create a reporting function for the current case</source>
        <translation>現在のcaseのためのレポーティングファンクションを作成します</translation>
    </message>
</context>
<context>
    <name>CfdOF_ScalarTransportFunctions</name>
    <message>
        <location filename="../CfdOF/Solve/CfdScalarTransportFunction.py" line="53"/>
        <source>Cfd scalar transport function</source>
        <translation>CFDスカラー輸送ファンクション</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdScalarTransportFunction.py" line="57"/>
        <source>Create a scalar transport function</source>
        <translation>スカラー輸送ファンクションを作成します</translation>
    </message>
</context>
<context>
    <name>CfdOF_SolverControl</name>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="55"/>
        <source>Solver job control</source>
        <translation>ソルバージョブ制御</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdSolverFoam.py" line="59"/>
        <source>Edit properties and run solver</source>
        <translation>プロパティを編集してソルバーを実行します</translation>
    </message>
</context>
<context>
    <name>CfdPreferencePage</name>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="14"/>
        <source>General</source>
        <translation>一般</translation>
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
        <translation>gmshの実行ファイルを絶対パスで指定します. システムの検索パスを使う場合には空白にします.</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="60"/>
        <source>The full path of the ParaView executable. Leave blank to use system search path or default install locations.</source>
        <translation>ParaViewの実行ファイルを絶対パスで指定します. システムの検索パスを使う場合や, デフォルトのインストール場所を使う場合には, 空白にします.</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="76"/>
        <source>OpenFOAM install directory</source>
        <translation>OpenFOAMのインストールディレクトリ</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="89"/>
        <source>ParaView executable</source>
        <translation>ParaViewの実行ファイル</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="109"/>
        <source>The OpenFOAM install folder. Leave blank to use $WM_PROJECT_DIR environment setting or standard install locations.</source>
        <translation>OpenFOAMをインストールしたフォルダを指定します. $WM_PROJECT_DIR環境変数を設定する場合や, 標準のインストール場所を使用する場合には, 空白にします.</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="142"/>
        <source>gmsh executable</source>
        <translation>gmshの実行ファイル</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="155"/>
        <source>Default output directory</source>
        <translation>デフォルトの出力ディレクトリ</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="165"/>
        <source>The directory to which case folders are written. Used unless overridden on a per-analysis basis. Use a &apos;.&apos; to denote the location of the current saved document, or leave blank to use a temporary directory.</source>
        <translation>caseフォルダを出力するディレクトリを指定します. 解析ごとに上書きされます. 現在の保存ディレクトリを使用する場合は &apos;.&apos; を入力し, 一時ディレクトリを使用する場合は空白にします.</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="175"/>
        <source>Create the output in a subdirectory with the name of the current saved document.</source>
        <translation>現在のドキュメント名と同じ名前のサブディレクトリの中に出力します.</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="178"/>
        <source>Append document name to output directory</source>
        <translation>ドキュメント名と同じ名前のサブディレクトリを作る</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="231"/>
        <source>Software dependencies</source>
        <translation>ソフトウェアの依存関係</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="241"/>
        <source>Run dependency checker</source>
        <translation>依存関係チェッカーを実行</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="263"/>
        <location filename="../Gui/CfdPreferencePage.ui" line="308"/>
        <location filename="../Gui/CfdPreferencePage.ui" line="373"/>
        <location filename="../Gui/CfdPreferencePage.ui" line="418"/>
        <source>Choose existing file ...</source>
        <translation>既存のファイルを選択...</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="270"/>
        <source>Install OpenFOAM</source>
        <translation>OpenFOAMをインストール</translation>
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
        <translation>ParaViewをインストール</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="360"/>
        <source>Install cfMesh</source>
        <translation>cfMeshをインストール</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="392"/>
        <source>Install HiSA</source>
        <translation>HiSAをインストール</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="431"/>
        <source>Docker Container</source>
        <translation>Dockerコンテナ</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="437"/>
        <source>Use Docker:</source>
        <translation>Dockerを使用する:</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="447"/>
        <source>Download from URL:</source>
        <translation>ダウンロード元のURL:</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="457"/>
        <source>Install Docker Image</source>
        <translation>Dockerイメージをインストール</translation>
    </message>
    <message>
        <location filename="../Gui/CfdPreferencePage.ui" line="489"/>
        <source>Output</source>
        <translation>出力</translation>
    </message>
</context>
<context>
    <name>Console</name>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidMaterial.py" line="61"/>
        <source>Set fluid properties 
</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdTools.py" line="1019"/>
        <source>Checking CFD workbench dependencies...
</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>Dialogs</name>
    <message>
        <location filename="../CfdOF/Mesh/TaskPanelCfdMesh.py" line="294"/>
        <location filename="../CfdOF/CfdPreferencePage.py" line="302"/>
        <location filename="../CfdOF/CfdTools.py" line="364"/>
        <source>CfdOF Workbench</source>
        <translation>CfdOFワークベンチ</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/TaskPanelCfdMesh.py" line="299"/>
        <source>The case setup for the mesher may need to be re-written based on changes you have made to the model.

Write mesh case first?</source>
        <translation>モデルの変更内容を踏まえると, メッシャー用のcase設定を保存し直した方が良さそうです.

最初にメッシュcaseを保存しますか?</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdPreferencePage.py" line="310"/>
        <source>Before installing this software, it is advised to run FreeCAD in administrator mode (hold down  the &apos;Shift&apos; key, right-click on the FreeCAD launcher, and choose &apos;Run as administrator&apos;).

If this is not possible, please make sure OpenFOAM is installed in a location to which you have full read/write access rights.

You are not currently running as administrator - do you wish to continue anyway?</source>
        <translation>このソフトウェアをインストールする前に, FreeCAD を管理者モードで実行することをお勧めします (Shift キーを押しながら FreeCAD ランチャーを右クリックし, 「管理者として実行」を選択してください).

管理者モードで実行できない場合は, OpenFOAM が完全な読み取り/書き込み権限を持つ場所にインストールされることを確認してください.

現在, 管理者として実行されていません. このまま続行しますか?</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/TaskPanelCfdMeshRefinement.py" line="186"/>
        <source>Mesh object not found - please re-create.</source>
        <translation>メッシュオブジェクトが見つかりません. 再作成してください.</translation>
    </message>
    <message>
        <location filename="../CfdOF/Mesh/TaskPanelCfdMeshRefinement.py" line="186"/>
        <source>Missing mesh object</source>
        <translation>メッシュオブジェクトがありません</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/TaskPanelCfdSolverControl.py" line="161"/>
        <source>The case may need to be re-meshed and the case setup re-written based on changes you have made to the model.

Re-mesh and re-write case setup first?</source>
        <translation>モデルの変更内容を踏まえると, メッシュの再作成とcase設定の再保存をした方が良さそうです.

最初にメッシュ再作成とcase設定の再保存を行いますか?</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/TaskPanelCfdSolverControl.py" line="167"/>
        <source>The case setup may need to be re-written based on changes you have made to the model.

Re-write case setup first?</source>
        <translation>モデルの変更内容を踏まえると, case設定を保存し直した方が良さそうです.

最初にcase設定の再保存を行いますか?</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/TaskPanelCfdSolverControl.py" line="175"/>
        <source>The case may need to be re-meshed based on changes you have made to the model.

Re-mesh case first?</source>
        <translation>モデルの変更内容を踏まえると, メッシュを作成し直した方が良さそうです.

最初にメッシュ再作成を行いますか?</translation>
    </message>
</context>
<context>
    <name>FilePicker</name>
    <message>
        <location filename="../CfdOF/CfdPreferencePage.py" line="244"/>
        <source>Choose OpenFOAM directory</source>
        <translation>OpenFOAMディレクトリを選択</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdPreferencePage.py" line="253"/>
        <source>Choose ParaView executable</source>
        <translation>ParaView実行ファイルを選択</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdPreferencePage.py" line="264"/>
        <source>Choose gmsh executable</source>
        <translation>gmsh実行ファイルを選択</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdPreferencePage.py" line="277"/>
        <source>Choose output directory</source>
        <translation>出力ディレクトリを選択</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdPreferencePage.py" line="325"/>
        <source>Choose OpenFOAM install file</source>
        <translation>OpenFOAMインストールファイルを選択</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdPreferencePage.py" line="338"/>
        <source>Choose ParaView install file</source>
        <translation>ParaViewインストールファイルを選択</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdPreferencePage.py" line="361"/>
        <source>Choose cfMesh archive</source>
        <translation>cfMeshアーカイブファイルを選択</translation>
    </message>
    <message>
        <location filename="../CfdOF/CfdPreferencePage.py" line="384"/>
        <source>Choose HiSA archive</source>
        <translation>HiSAアーカイブファイルを選択</translation>
    </message>
</context>
<context>
    <name>Subnames</name>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="58"/>
        <source>No-slip (viscous)</source>
        <translation>ノースリップ (粘性) / No-slip (viscous)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="59"/>
        <source>Slip (inviscid)</source>
        <translation>スリップ (非粘性) / Slip (inviscid)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="60"/>
        <source>Partial slip</source>
        <translation>部分的スリップ / Partial slip</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="61"/>
        <source>Rotating</source>
        <translation>回転 / Rotating</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="62"/>
        <source>Translating</source>
        <translation>平行移動 / Translating</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="63"/>
        <source>Rough</source>
        <translation>粗い壁面 / Rough</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="65"/>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="73"/>
        <source>Uniform velocity</source>
        <translation>一様速度 / Uniform velocity</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="66"/>
        <source>Volumetric flow rate</source>
        <translation>体積流量 / Volumetric flow rate</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="67"/>
        <source>Mass flow rate</source>
        <translation>質量流量 / Mass flow rate</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="68"/>
        <source>Total pressure</source>
        <translation>全圧 / Total pressure</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="69"/>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="72"/>
        <source>Static pressure</source>
        <translation>静圧 / Static pressure</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="74"/>
        <source>Extrapolated</source>
        <translation>外挿 / Extrapolated</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="76"/>
        <source>Ambient pressure</source>
        <translation>周囲圧力 / Ambient pressure</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="76"/>
        <source>Far-field</source>
        <translation>遠方境界 / Far-field</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="77"/>
        <source>Symmetry</source>
        <translation>対称 / Symmetry</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="77"/>
        <source>Periodic</source>
        <translation>周期 / Periodic</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="78"/>
        <source>Porous Baffle</source>
        <translation>多孔質バッフル / Porous Baffle</translation>
    </message>
</context>
<context>
    <name>Subtypes</name>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="100"/>
        <source>Zero velocity relative to wall</source>
        <translation>壁面近傍の流れがゼロ (滑りなし)</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="101"/>
        <source>Frictionless wall; zero normal velocity</source>
        <translation>摩擦のない壁面 (滑りあり); 壁面に対して法線方向への速度がゼロ</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="102"/>
        <source>Blended fixed/slip</source>
        <translation>固定/スリップのブレンド</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="103"/>
        <source>Fixed velocity corresponding to rotation about an axis</source>
        <translation>一定速度で軸回転</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="104"/>
        <source>Fixed velocity tangential to wall; zero normal velocity</source>
        <translation>壁面に対して接線方向には一定速度、壁面に対して法線方向には速度がゼロ</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="105"/>
        <source>Wall roughness function</source>
        <translation>壁面の粗さの関数</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="106"/>
        <source>Velocity specified; normal component imposed for reverse flow</source>
        <translation>速度を指定する; 逆流が生じる場合には法線方向の速度成分が適用される</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="107"/>
        <source>Uniform volume flow rate specified</source>
        <translation>一様な体積流量を指定する</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="108"/>
        <source>Uniform mass flow rate specified</source>
        <translation>一様な質量流量を指定する</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="111"/>
        <source>Total pressure specified; treated as static pressure for reverse flow</source>
        <translation>全圧を指定する; 逆流が生じる場合には静圧として扱われる</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="112"/>
        <source>Static pressure specified</source>
        <translation>静圧を指定する</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="117"/>
        <source>Static pressure specified for outflow and total pressure for reverse flow</source>
        <translation>流出に静圧を指定する; 逆流が生じる場合には全圧として適用される</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="120"/>
        <source>Normal component imposed for outflow; velocity fixed for reverse flow</source>
        <translation>流出には法線速度を課し, 逆流が生じる場合には速度が固定される</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="121"/>
        <source>All fields extrapolated; possibly unstable</source>
        <translation>全フィールドを外挿する; 不安定になる可能性あり</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="124"/>
        <source>Boundary open to surroundings with total pressure specified</source>
        <translation>外部に開放, 全圧を指定する</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="125"/>
        <source>Characteristic-based non-reflecting boundary</source>
        <translation>特性に基づく非反射境界</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="128"/>
        <source>Symmetry of flow quantities about boundary face</source>
        <translation>境界面を中心に流れの物理量が対称</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="131"/>
        <source>Rotationally or translationally periodic flows between two boundary faces</source>
        <translation>2つの境界面間での回転または平行方向の周期的流れ</translation>
    </message>
    <message>
        <location filename="../CfdOF/Solve/CfdFluidBoundary.py" line="133"/>
        <source>Permeable screen</source>
        <translation>透過性スクリーン</translation>
    </message>
</context>
<context>
    <name>TaskPanelCfdDynamicMeshInterfaceRefinement</name>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshInterfaceRefinement.ui" line="14"/>
        <source>Dynamic Mesh</source>
        <translation>動的メッシュ</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshInterfaceRefinement.ui" line="35"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Write refinement cell level scalar at each solver write iteration&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>ソルバーの各出力タイミングで細分化セルレベルのスカラー値を書き出す</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshInterfaceRefinement.ui" line="38"/>
        <source>Output refinement level field</source>
        <translation>細分化レベルを記録するフィールドを出力</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshInterfaceRefinement.ui" line="69"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Iteration interval at which to perform dynamic mesh refinement&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>動的メッシュ細分化を行う反復インターバル</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshInterfaceRefinement.ui" line="91"/>
        <source>Refinement interval</source>
        <translation>細分化のインターバル</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshInterfaceRefinement.ui" line="98"/>
        <source>Max refinement level</source>
        <translation>最大細分化レベル</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshInterfaceRefinement.ui" line="105"/>
        <source>Refine interface of</source>
        <translation>細分化するインターフェース</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshInterfaceRefinement.ui" line="115"/>
        <source>Buffer layers</source>
        <translation>バッファーレイヤー</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshInterfaceRefinement.ui" line="122"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Maximum number of levels of refinement to apply&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>メッシュ細分化の最大レベル数</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshInterfaceRefinement.ui" line="141"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Number of cells layers between refinement and existing cells&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>細分化セルと既存セルの間のセル層数</translation>
    </message>
</context>
<context>
    <name>TaskPanelCfdDynamicMeshRefinement</name>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshShockRefinement.ui" line="14"/>
        <source>Dynamic Mesh</source>
        <translation>動的メッシュ</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshShockRefinement.ui" line="35"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Write refinement cell level scalar at each solver write iteration&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>ソルバーの各出力タイミングで細分化セルレベルのスカラー値を書き出す</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshShockRefinement.ui" line="38"/>
        <source>Output refinement field</source>
        <translation>細分化を記録するフィールドを出力</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshShockRefinement.ui" line="69"/>
        <source>Refinement interval</source>
        <translation>細分化レベル</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshShockRefinement.ui" line="76"/>
        <source>Buffer layers</source>
        <translation>バッファーレイヤー</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshShockRefinement.ui" line="83"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Number of cells layers between refinement and existing cells&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>細分化セルと既存セルの間のセル層数</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshShockRefinement.ui" line="96"/>
        <source>Typically the far-field or input velocity (direction only)</source>
        <translation>通常は遠方境界(far-field)または入力速度(方向のみ)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshShockRefinement.ui" line="99"/>
        <source>Reference velocity direction</source>
        <translation>速度方向の参照値</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshShockRefinement.ui" line="106"/>
        <source>Relative element size</source>
        <translation>相対的な要素サイズ</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshShockRefinement.ui" line="113"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Maximum number of levels of refinement to apply&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>メッシュ細分化の最大レベル数</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdDynamicMeshShockRefinement.ui" line="132"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Iteration interval at which to perform dynamic mesh refinement&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>動的メッシュ細分化を行う反復インターバル</translation>
    </message>
</context>
<context>
    <name>TaskPanelCfdFluidBoundary</name>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="14"/>
        <source>CFD boundary condition</source>
        <translation>CFD境界条件</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="62"/>
        <source>Boundary </source>
        <translation>境界</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="85"/>
        <source>Sub-type</source>
        <translation>サブタイプ</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="102"/>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="681"/>
        <source>Description </source>
        <translation>説明</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="112"/>
        <source>Help text</source>
        <translation>ヘルプテキスト</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="130"/>
        <source>Boundary face list</source>
        <translation>境界面のリスト</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="188"/>
        <source>Turbulence specification</source>
        <translation>乱流の定義</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="235"/>
        <source>Turbulent kinetic energy (k)</source>
        <translation>運動エネルギー (k)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="270"/>
        <source>Dissipation rate (ε)</source>
        <translation>散逸率 (ε)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="305"/>
        <source>Specific dissipation rate (ω)</source>
        <translation>比散逸率 (ω)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="340"/>
        <source>Turbulence intensity (I)</source>
        <translation>強度 (I)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="427"/>
        <source>Length scale (l)</source>
        <translation>長さスケール (l)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="462"/>
        <source>Modified turbulent viscosity (ṽ)</source>
        <translation>変形乱流粘性 (ṽ)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="497"/>
        <source>Intermittency (γ)</source>
        <translation>乱流の間欠度 (γ)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="532"/>
        <source>Momentum Thickness (Reθ)</source>
        <translation>運動量厚さ (Reθ)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="567"/>
        <source>Turbulent viscosity (v)</source>
        <translation>乱流粘性 (v)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="625"/>
        <source>Thermal</source>
        <translation>熱的条件</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="691"/>
        <source>Heat flux</source>
        <translation>熱流束</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="704"/>
        <source>Type</source>
        <translation>タイプ</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="736"/>
        <source>Temperature</source>
        <translation>温度</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="771"/>
        <source>Heat transfer coefficient</source>
        <translation>熱伝達係数</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="825"/>
        <source>Velocity</source>
        <translation>速度</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="846"/>
        <source>Car&amp;tesian components</source>
        <translation>カルテシアン成分</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="853"/>
        <source>Ma&amp;gnitude and normal</source>
        <translation>法線方向と大きさ</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="988"/>
        <source>Magnitude</source>
        <translation>大きさ</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1023"/>
        <source>Normal to face</source>
        <translation>この面に対して法線方向</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1051"/>
        <source>Pick</source>
        <translation>選択</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1075"/>
        <source>Inward normal</source>
        <translation>内向き法線</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1109"/>
        <source>Pressure</source>
        <translation>圧力</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1165"/>
        <source>Slip ratio (0.0 - 1.0)</source>
        <translation>スリップ比率 (0.0 - 1.0)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1227"/>
        <source>Volume flow rate</source>
        <translation>体積流量</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1283"/>
        <source>Mass flow rate</source>
        <translation>質量流量</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1342"/>
        <source>Porous resistance:</source>
        <translation>多孔質抵抗:</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1349"/>
        <source>Pressure &amp;loss coefficient</source>
        <translation>圧力損失係数</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1359"/>
        <source>Wire screen parameters</source>
        <translation>ワイヤースクリーンパラメータ</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1394"/>
        <source>Pressure loss coefficient</source>
        <translation>圧力損失係数</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1448"/>
        <source>Wire diameter</source>
        <translation>線径</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1483"/>
        <source>Spacing</source>
        <translation>間隔</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1549"/>
        <source>Roughness height (Ks)</source>
        <translation>粗さの高さ (Ks)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1578"/>
        <source>Roughness constant (Cs)</source>
        <translation>粗さの係数 (Cs)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1634"/>
        <source>Relative to rotating frame</source>
        <translation>回転フレームに対して相対的</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1665"/>
        <source>Rotation axis</source>
        <translation>回転軸の方向</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1672"/>
        <source>Rotation origin</source>
        <translation>回転の基準点</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1679"/>
        <source>Angular velocity</source>
        <translation>角速度</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1682"/>
        <source>Slave patch</source>
        <translation>スレーブパッチ</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1692"/>
        <source>Master patch</source>
        <translation>マスターパッチ</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1708"/>
        <source>Periodic</source>
        <translation>周期</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1742"/>
        <source>Partner patch</source>
        <translation>パートナーパッチ</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1773"/>
        <source>Translational</source>
        <translation>平行移動</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1783"/>
        <source>Rotational</source>
        <translation>回転</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1817"/>
        <source>Centre of rotation</source>
        <translation>回転の基準点</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="1824"/>
        <source>Rotational axis</source>
        <translation>回転軸の方向</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="2008"/>
        <source>Separation vector</source>
        <translation>分離ベクトル</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="2108"/>
        <source>Fluid</source>
        <translation>流体</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="2115"/>
        <source>The proportion of each computational cell composed of the fluid selected.</source>
        <translation>各計算セル内における選択された流体の割合.</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="2118"/>
        <source>Volume fraction</source>
        <translation>体積分率</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="2156"/>
        <source>Inflow Volume Fractions</source>
        <translation>流入体積分率</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidBoundary.ui" line="2166"/>
        <source>Use as default boundary condition for unselected faces</source>
        <translation>デフォルトの境界条件として使用する (境界条件が設定されていない面に適用)</translation>
    </message>
</context>
<context>
    <name>TaskPanelCfdFluidProperties</name>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidProperties.ui" line="14"/>
        <location filename="../Gui/TaskPanelCfdFluidProperties.ui" line="42"/>
        <source>Fluid properties</source>
        <translation>流体物性</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidProperties.ui" line="29"/>
        <source>Compressible</source>
        <translation>圧縮可能</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidProperties.ui" line="130"/>
        <source>Material name</source>
        <translation>マテリアル名</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidProperties.ui" line="149"/>
        <source>Material Description</source>
        <translation>マテリアルの説明</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidProperties.ui" line="166"/>
        <source>Predefined fluid library</source>
        <translation>定義済み流体ライブラリ</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdFluidProperties.ui" line="176"/>
        <source>Save...</source>
        <translation>保存...</translation>
    </message>
</context>
<context>
    <name>TaskPanelCfdInitialiseInternalField</name>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="14"/>
        <source>Initialise flow field</source>
        <translation>流れ場の初期化</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="35"/>
        <source>Turbulence</source>
        <translation>乱流</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="45"/>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="659"/>
        <source>Use values from boundary</source>
        <translation>境界の値を使用</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="310"/>
        <source>Reθ</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="510"/>
        <source>Temperature:</source>
        <translation>温度:</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="536"/>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="837"/>
        <source>Use value from boundary</source>
        <translation>境界の値を使用</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="573"/>
        <source>Thermal</source>
        <translation>熱的条件</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="601"/>
        <source>Volume Fractions</source>
        <translation>体積分率</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="608"/>
        <source>Fluid</source>
        <translation>流体</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="615"/>
        <source>The proportion of each computational cell composed of the fluid selected.</source>
        <translation>各計算セル内における選択された流体の割合.</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="618"/>
        <source>Volume fraction</source>
        <translation>体積分率</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="768"/>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="823"/>
        <source>Potential flow</source>
        <translation>ポテンシャル流れ</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="775"/>
        <source>Specify values</source>
        <translation>値を指定</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="788"/>
        <source>Velocity</source>
        <translation>速度</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="816"/>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="865"/>
        <source>Pressure</source>
        <translation>圧力</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdInitialiseInternalField.ui" line="830"/>
        <source>Specify value</source>
        <translation>値を指定</translation>
    </message>
</context>
<context>
    <name>TaskPanelCfdListOfFaces</name>
    <message>
        <location filename="../Gui/TaskPanelCfdListOfFaces.ui" line="14"/>
        <source>Select Faces</source>
        <translation>面を選択</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdListOfFaces.ui" line="36"/>
        <source>Select in model</source>
        <translation>モデルから選択</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdListOfFaces.ui" line="83"/>
        <source>So&amp;lid</source>
        <translation>ソリッド</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdListOfFaces.ui" line="90"/>
        <source>Face, Ed&amp;ge, Vertex</source>
        <translation>面, エッジ, 頂点</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdListOfFaces.ui" line="100"/>
        <source>Remove</source>
        <translation>除外</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdListOfFaces.ui" line="107"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Selection&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>選択</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdListOfFaces.ui" line="114"/>
        <source>Add</source>
        <translation>追加</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdListOfFaces.ui" line="122"/>
        <source>Select from list</source>
        <translation>リストから選択</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdListOfFaces.ui" line="131"/>
        <source>Select objects</source>
        <translation>オブジェクトを選択</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdListOfFaces.ui" line="147"/>
        <source>Select all</source>
        <translation>すべて選択</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdListOfFaces.ui" line="154"/>
        <source>Select none</source>
        <translation>すべて選択しない</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdListOfFaces.ui" line="194"/>
        <source>▼ Select components</source>
        <translation>コンポーネントを選択</translation>
    </message>
</context>
<context>
    <name>TaskPanelCfdMesh</name>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="14"/>
        <source>CFD Mesh</source>
        <translation>CFDメッシュ</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="46"/>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="59"/>
        <source>Mesh Parameters</source>
        <translation>メッシュパラメータ</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="66"/>
        <source>Mesh utility:</source>
        <translation>メッシュユーティリティ:</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="73"/>
        <source>Base element size:</source>
        <translation>基本要素サイズ:</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="138"/>
        <source>Search</source>
        <translation>検索</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="244"/>
        <source>Point in mesh</source>
        <translation>メッシュ内の点</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="275"/>
        <source>Edge detection</source>
        <translation>エッジ検出</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="282"/>
        <source>Implicit</source>
        <translation>暗黙的</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="289"/>
        <source>Explicit</source>
        <translation>明示的</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="322"/>
        <source>No of cells between levels</source>
        <translation>レベル間のセル数</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="329"/>
        <source>Relative edge refinement</source>
        <translation>相対エッジ細分化</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="359"/>
        <source>Stop</source>
        <translation>停止</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="366"/>
        <source>Run mesher</source>
        <translation>メッシャーの実行</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="379"/>
        <source>Meshing</source>
        <translation>メッシュ作成</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="386"/>
        <source>Write mesh case</source>
        <translation>メッシュcaseの保存</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="393"/>
        <source>Edit</source>
        <translation>編集</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="422"/>
        <source>Clear</source>
        <translation>クリア</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="429"/>
        <source> Load surface mesh</source>
        <translation>サーフェスメッシュの読み込み</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="442"/>
        <source>Visualisation</source>
        <translation>可視化</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="456"/>
        <source>Check Mesh</source>
        <translation>メッシュのチェック</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMesh.ui" line="482"/>
        <source>Status</source>
        <translation>状態</translation>
    </message>
</context>
<context>
    <name>TaskPanelCfdMeshRefinement</name>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="14"/>
        <source>Mesh refinement</source>
        <translation>メッシュ細分化</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="35"/>
        <source>Volume refinement</source>
        <translation>ボリュームの細分化</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="42"/>
        <source>Surface refinement</source>
        <translation>表面の細分化</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="52"/>
        <source>Extrusion</source>
        <translation>押し出し</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="83"/>
        <source>Relative element size</source>
        <translation>相対的な要素サイズ</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="124"/>
        <source>Refinement thickness</source>
        <translation>細分化の厚さ</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="131"/>
        <source>Boundary layers</source>
        <translation>境界層</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="200"/>
        <source>Expansion ratio:</source>
        <translation>膨張比率:</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="224"/>
        <source>Number of layers:</source>
        <translation>レイヤー数</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="242"/>
        <source>Max first cell height (optional):</source>
        <translation>初層セルの最大高さ (オプション):</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="386"/>
        <source>Edge refinement level</source>
        <translation>エッジの細分化レベル</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="414"/>
        <source>Extrusion type</source>
        <translation>押し出しタイプ</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="424"/>
        <source>Keep existing mesh</source>
        <translation>既存のメッシュを維持</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="431"/>
        <source>Thickness</source>
        <translation>厚さ</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="451"/>
        <source>Angle</source>
        <translation>角度</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="471"/>
        <source>Number of layers</source>
        <translation>層数</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="488"/>
        <source>Expansion ratio</source>
        <translation>拡大率</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="578"/>
        <source>Axis point</source>
        <translation>回転の基準点</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="598"/>
        <source>Copy from selected edge</source>
        <translation>選択したエッジからコピー</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="605"/>
        <source>Axis direction</source>
        <translation>回転軸の方向</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="700"/>
        <location filename="../Gui/TaskPanelCfdMeshRefinement.ui" line="756"/>
        <source>References</source>
        <translation>リファレンス</translation>
    </message>
</context>
<context>
    <name>TaskPanelCfdReportingFunctions</name>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="14"/>
        <source>CFD reporting function</source>
        <translation>CFDレポーティングファンクション</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="55"/>
        <source>Reporting function</source>
        <translation>レポーティングファンクション</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="72"/>
        <source>Description </source>
        <translation>説明</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="82"/>
        <source>Help text</source>
        <translation>ヘルプテキスト</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="131"/>
        <source>Parameters</source>
        <translation>パラメータ</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="236"/>
        <source>Centre of rotation</source>
        <translation>回転の基準点</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="249"/>
        <source>Write fields</source>
        <translation>フィールドの書き込み</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="284"/>
        <source>Relative pressure reference</source>
        <translation>相対圧力の参照値</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="314"/>
        <source>Coefficients</source>
        <translation>係数</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="335"/>
        <source>Lift Direction</source>
        <translation>揚力方向</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="526"/>
        <source>Free-stream flow speed</source>
        <translation>自由流れの流速</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="533"/>
        <source>Reference length</source>
        <translation>長さの参照値</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="540"/>
        <source>Reference area</source>
        <translation>面積の参照値</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="603"/>
        <source>Drag Direction</source>
        <translation>抗力方向</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="610"/>
        <source>Free-stream density</source>
        <translation>自由流れの密度</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="665"/>
        <source>Patch list</source>
        <translation>パッチリスト</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="683"/>
        <source>Patches                          </source>
        <translation>パッチ</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="716"/>
        <source>Spatial data binning</source>
        <translation>空間データのビニング</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="737"/>
        <source>Number of bins</source>
        <translation>ビンの数</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="831"/>
        <source>Binning direction</source>
        <translation>ビニング方向</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="844"/>
        <source>Cumulative</source>
        <translation>累積値</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="911"/>
        <source>Sample field name</source>
        <translation>サンプルフィールド名</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdReportingFunctions.ui" line="997"/>
        <source>Probe location (x, y, z)</source>
        <translation>プローブ位置 (x, y, z)</translation>
    </message>
</context>
<context>
    <name>TaskPanelCfdScalarTransportFunctions</name>
    <message>
        <location filename="../Gui/TaskPanelCfdScalarTransportFunctions.ui" line="14"/>
        <source>Scalar transport function</source>
        <translation>スカラー輸送ファンクション</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdScalarTransportFunctions.ui" line="52"/>
        <source>Scalar Transport</source>
        <translation>スカラー輸送</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdScalarTransportFunctions.ui" line="70"/>
        <source>Viscous/turbulent</source>
        <translation>粘性/乱流</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdScalarTransportFunctions.ui" line="77"/>
        <source>Scalar field name</source>
        <translation>スカラーフィールド名</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdScalarTransportFunctions.ui" line="84"/>
        <source>Specified coefficient</source>
        <translation>指定された係数</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdScalarTransportFunctions.ui" line="135"/>
        <source>Restrict to phase</source>
        <translation>フェーズを制限</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdScalarTransportFunctions.ui" line="145"/>
        <source>Diffusivity</source>
        <translation>拡散率</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdScalarTransportFunctions.ui" line="160"/>
        <source>Scalar injection</source>
        <translation>スカラーインジェクション</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdScalarTransportFunctions.ui" line="269"/>
        <source>Injection point (x, y, z)</source>
        <translation>インジェクション点 (x, y, z)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdScalarTransportFunctions.ui" line="282"/>
        <source>Injection rate</source>
        <translation>インジェクション率</translation>
    </message>
</context>
<context>
    <name>TaskPanelCfdSolverControl</name>
    <message>
        <location filename="../Gui/TaskPanelCfdSolverControl.ui" line="14"/>
        <source>Analysis control</source>
        <translation>解析のコントロール</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdSolverControl.ui" line="40"/>
        <source>Write</source>
        <translation>保存</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdSolverControl.ui" line="50"/>
        <source>Edit</source>
        <translation>編集</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdSolverControl.ui" line="63"/>
        <source>Case setup</source>
        <translation>Case設定</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdSolverControl.ui" line="95"/>
        <source>Stop</source>
        <translation>停止</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdSolverControl.ui" line="105"/>
        <source>Run</source>
        <translation>実行</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdSolverControl.ui" line="118"/>
        <source>Solver</source>
        <translation>ソルバー</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdSolverControl.ui" line="176"/>
        <source>Results</source>
        <translation>結果</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdSolverControl.ui" line="199"/>
        <source>Status</source>
        <translation>状態</translation>
    </message>
</context>
<context>
    <name>TaskPanelCfdZone</name>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="14"/>
        <source>CFD Zone</source>
        <translation>CFDゾーン</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="55"/>
        <source>Correspond to directions in which the velocity is scaled but not rotated by the porous medium</source>
        <translation>多孔質媒体によって速度が回転されずにスケーリングされる方向に対応</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="58"/>
        <source>Principal directions</source>
        <translation>主要方向</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="152"/>
        <source>Porous drag coefficients in principal directions</source>
        <translation>主要方向の多孔質抗力係数</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="396"/>
        <source>Viscous (d)</source>
        <translation>粘性 (d)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="434"/>
        <source>Inertial (f)</source>
        <translation>慣性 (f)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="546"/>
        <source>Porous correlation</source>
        <translation>多孔質相関モデル</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="565"/>
        <source>Tube outer diameter</source>
        <translation>チューブの外径</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="594"/>
        <source>Longitudinal axis of the tube</source>
        <translation>チューブの長手方向</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="597"/>
        <source>Tube axis</source>
        <translation>チューブの軸の方向</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="685"/>
        <source>Spacing between tubes normal to layers</source>
        <translation>層に垂直なチューブの間隔</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="688"/>
        <source>Tube spacing</source>
        <translation>チューブの間隔</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="720"/>
        <source>Direction of spacing normal to layers</source>
        <translation>層に垂直な間隔の方向</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="723"/>
        <source>Spacing direction</source>
        <translation>チューブの間隔の方向</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="793"/>
        <source>Multiplier used to obtain spacing perpendicular to spacing direction</source>
        <translation>配列方向に垂直な方向の間隔倍率</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="796"/>
        <source>Spacing aspect ratio</source>
        <translation>間隔のアスペクト比</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="852"/>
        <source>Estimated incident (superficial) velocity used for Reynolds number adjustment of correlation.</source>
        <translation>レイノルズ数調整に用いる見かけ流速 (推定値)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="855"/>
        <source>Velocity estimate</source>
        <translation>推定速度</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="899"/>
        <source>Set velocity</source>
        <translation>速度の設定</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="936"/>
        <source>Set volume fractions</source>
        <translation>体積分率の設定</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="1044"/>
        <source>Set pressure</source>
        <translation>圧力の設定</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelCfdZone.ui" line="1072"/>
        <source>Set temperature</source>
        <translation>温度の設定</translation>
    </message>
</context>
<context>
    <name>TaskPanelPhysics</name>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="14"/>
        <source>Select physics model</source>
        <translation>物理モデルを選択</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="44"/>
        <source>Stead&amp;y</source>
        <translation>定常 / Stead&amp;y</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="57"/>
        <source>&amp;Transient</source>
        <translation>非定常 / &amp;Transient</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="70"/>
        <source>Time</source>
        <translation>時間の扱い</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="170"/>
        <source>Moving reference frame (SRF)</source>
        <translation>移動座標系 (SRF)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="177"/>
        <source>RPM</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="184"/>
        <source>Rotational axis</source>
        <translation>回転軸の方向</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="213"/>
        <source>Centre of rotation</source>
        <translation>回転の基準点</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="313"/>
        <source>Flow</source>
        <translation>フロー</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="347"/>
        <source>Isothermal</source>
        <translation>等温</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="360"/>
        <source>High Mach number</source>
        <translation>高いマッハ数</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="370"/>
        <source>Rotating frame (SRF)</source>
        <translation>移動座標系 (SRF)</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="404"/>
        <source>Single phase</source>
        <translation>単相流</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="417"/>
        <source>Multiphase - free surface</source>
        <translation>混相流 - 自由表面</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="430"/>
        <source>Viscous</source>
        <translation>粘性</translation>
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
        <translation>モデル</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="589"/>
        <source>Turbulence</source>
        <translation>乱流</translation>
    </message>
    <message>
        <location filename="../Gui/TaskPanelPhysics.ui" line="695"/>
        <source>Gravity</source>
        <translation>重力</translation>
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
        <translation>CfdOFワークベンチ</translation>
    </message>
    <message>
        <location filename="../InitGui.py" line="96"/>
        <source>Dynamic mesh refinement</source>
        <translation>動的なメッシュ細分化</translation>
    </message>
    <message>
        <location filename="../InitGui.py" line="105"/>
        <source>Development</source>
        <translation>開発</translation>
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
