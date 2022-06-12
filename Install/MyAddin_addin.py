# coding=utf-8
import arcpy
import pythonaddins
import os
import shutil

arcpy.env.overwriteOutput = True

fileName = ''
filePath = ''
mxd = None
demLayer = None
row = 2
col = 2


def extract(input, mask, output):
    rmask = arcpy.Raster(mask)
    rmask = arcpy.sa.Times(rmask, 0)
    rinput = arcpy.Raster(input)
    rOutput = arcpy.sa.Plus(rinput, rmask)
    rOutput.save(output)


class MyValidator(object):
    def __str__(self):
        return "TIFF(*.tif)| IMAGINE Image(*.img)"

    def __call__(self, filename):
        if os.path.isdir(filename):
            return True
        basename = os.path.basename(filename)
        if basename.endswith(".tif") or basename.endswith(".img"):
            return True
        else:
            return False


class ExportValidator(object):
    def __str__(self):
        return "PNG(*.png)"

    def __call__(self, fileName):
        if os.path.isdir(fileName):
            return False
        baseName = os.path.basename(fileName)
        if baseName.endswith(".png"):
            return True
        else:
            return False


class AspectBt(object):
    """Implementation for MyAddin_addin.button_2 (Button)"""

    def __init__(self):
        self.enabled = True
        self.checked = False

    def onClick(self):
        outFolder = os.path.join(filePath, "SplitRaster")
        blockFiles = os.listdir(outFolder)
        blockFiles = filter(lambda blockFile: blockFile.endswith('.IMG'), blockFiles)
        aspectFolder = os.path.join(filePath, "Aspect")
        if os.path.exists(aspectFolder):
            shutil.rmtree(aspectFolder)
        os.makedirs(aspectFolder)
        aspectFiles = []
        for blockFile in blockFiles:
            blockFilePath = os.path.join(outFolder, blockFile)
            blockAspect = arcpy.sa.Aspect(blockFilePath)
            blockAspectPath = os.path.join(aspectFolder, blockFile)
            blockAspect.save(blockAspectPath)
            aspectFiles.append(blockAspectPath)
        # 栅格拼接
        aspectFiles = ';'.join(aspectFiles)
        baseName = os.path.basename(fileName)[0:-4]
        aspectFilesMosaic = os.path.join(filePath, "{}_aspect.img".format(baseName))
        if os.path.exists(aspectFilesMosaic):
            os.remove(aspectFilesMosaic)
        arcpy.env.mask = fileName
        arcpy.MosaicToNewRaster_management(
            input_rasters=aspectFiles,
            output_location=filePath, raster_dataset_name_with_extension="{}_aspect.img".format(baseName),
            coordinate_system_for_the_raster="", pixel_type="32_BIT_FLOAT", cellsize="", number_of_bands="1",
            mosaic_method="MEAN", mosaic_colormap_mode="FIRST")
        aspectFilesMosaicClip = os.path.join(filePath, "{}_aspect_clip.img".format(baseName))
        extract(aspectFilesMosaic, fileName, aspectFilesMosaicClip)
        aspectLayer = arcpy.mapping.Layer(aspectFilesMosaicClip)
        df = arcpy.mapping.ListDataFrames(mxd)[0]
        arcpy.mapping.AddLayer(df, aspectLayer)


class BlockBt(object):
    """Implementation for MyAddin_addin.button_1 (Button)"""

    def __init__(self):
        self.enabled = True
        self.checked = False

    def onClick(self):
        global filePath
        if not (fileName):
            return
        filePath = os.path.dirname(fileName)
        baseName = os.path.basename(fileName)[0:-4]
        outFolder = os.path.join(filePath, 'SplitRaster')
        if os.path.exists(outFolder):
            shutil.rmtree(outFolder)
        os.makedirs(outFolder)
        arcpy.env.parallelProcessingFactor = 1
        arcpy.SplitRaster_management(in_raster=fileName, out_folder=outFolder, out_base_name=baseName,
                                     split_method="NUMBER_OF_TILES", format="IMAGINE IMAGE", resampling_type="NEAREST",
                                     num_rasters="{} {}".format(col, row), tile_size="2048 2048", overlap="0",
                                     units="PIXELS", cell_size="", origin="", split_polygon_feature_class="",
                                     clip_type="NONE", template_extent="DEFAULT", nodata_value="#")

        #       加载分割后的数据
        n = int(col) * int(row)
        for i in range(n):
            blockFileName = os.path.join(outFolder, '{}{}.IMG'.format(baseName, i))
            blockLayer = arcpy.mapping.Layer(blockFileName)
            df = arcpy.mapping.ListDataFrames(mxd)[0]
            arcpy.mapping.AddLayer(df, blockLayer)
        # 重置并行处理因子
        arcpy.env.parallelProcessingFactor = ""


class ClassifyBt(object):
    """Implementation for MyAddin_addin.button_3 (Button)"""

    def __init__(self):
        self.enabled = True
        self.checked = False

    def onClick(self):
        baseName = os.path.basename(fileName)[0:-4]
        aspectFilesMosaicClip = os.path.join(filePath, "{}_aspect_clip.img".format(baseName))
        classifyASCII = os.path.join(os.path.dirname(__file__), "classify.txt")
        aspectClassify = arcpy.sa.ReclassByASCIIFile(aspectFilesMosaicClip, classifyASCII, missing_values='NODATA')
        aspectClassifyFile = os.path.join(filePath, "{}_aspect_classify.img".format(baseName))
        aspectClassify.save(aspectClassifyFile)
        aspectClassifyClipFile = os.path.join(filePath, "{}_aspect_classify_clip.img".format(baseName))
        extract(aspectClassifyFile, fileName, aspectClassifyClipFile)
        df = arcpy.mapping.ListDataFrames(mxd)[0]
        aspectClassifyLayer = arcpy.mapping.Layer(aspectClassifyClipFile)
        arcpy.mapping.AddLayer(df, aspectClassifyLayer)
        aspectSymbol = os.path.join(os.path.dirname(__file__), "aspect.lyr")
        arcpy.ApplySymbologyFromLayer_management("{}_aspect_classify_clip.img".format(baseName), aspectSymbol)


class ColComboBox(object):
    """Implementation for MyAddin_addin.combobox_1 (ComboBox)"""

    def __init__(self):
        self.items = ['2', '3', '4']
        self.editable = True
        self.enabled = True
        self.dropdownWidth = 'WWWWWW'
        self.width = 'WWWWWW'

    def onSelChange(self, selection):
        global col
        col = selection
        pass

    def onEditChange(self, text):
        pass

    def onFocus(self, focused):
        pass

    def onEnter(self):
        pass

    def refresh(self):
        pass


class ExportBt(object):
    """Implementation for MyAddin_addin.button_4 (Button)"""

    def __init__(self):
        self.enabled = True
        self.checked = False

    def onClick(self):
        baseName = os.path.basename(fileName)[0:-4]
        exportName = pythonaddins.SaveDialog("Export Map", "{}.png".format(baseName), filePath, ExportValidator())
        if exportName:
            templateMxdFile = os.path.join(os.path.dirname(__file__), 'template.mxd')
            templateMxd = arcpy.mapping.MapDocument(templateMxdFile)
            layer = arcpy.mapping.ListLayers(templateMxd)[0]
            layer.replaceDataSource(workspace_path=filePath, workspace_type='RASTER_WORKSPACE',
                                    dataset_name="{}_aspect_classify_clip.img".format(baseName))
            arcpy.mapping.ExportToPNG(templateMxd, exportName)
        return


class LoadBt(object):
    """Implementation for MyAddin_addin.button (Button)"""

    def __init__(self):
        self.enabled = True
        self.checked = False

    def onClick(self):
        global fileName, mxd, demLayer
        fileName = pythonaddins.OpenDialog("Select files to process", False, '', 'Open', MyValidator())
        if fileName:
            mxd = arcpy.mapping.MapDocument('CURRENT')
            df = arcpy.mapping.ListDataFrames(mxd)[0]
            demLayer = arcpy.mapping.Layer(fileName)
            arcpy.mapping.AddLayer(df, demLayer)
            arcpy.env.mask = fileName
        return


class RowComboBox(object):
    """Implementation for MyAddin_addin.combobox (ComboBox)"""

    def __init__(self):
        self.items = ['2', '3', '4']
        self.editable = True
        self.enabled = True
        self.dropdownWidth = 'WWWWWW'
        self.width = 'WWWWWW'

    def onSelChange(self, selection):
        global row
        row = selection
        pass

    def onEditChange(self, text):
        pass

    def onFocus(self, focused):
        pass

    def onEnter(self):
        pass

    def refresh(self):
        pass
