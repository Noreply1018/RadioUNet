# RadioMapSeer 数据集校验报告

- dataset_dir: `/root/lanyun-tmp/projects/RadioUNet_hkf/RadioMapSeer`
- passed: `True`

## 必要目录
- OK: `png/buildings_complete`，png=701
- OK: `png/antennas`，png=56080
- OK: `gain/DPM`，png=56080
- OK: `gain/IRT2`，png=56080
- OK: `gain/IRT4`，png=1402

## 可选目录
- OK: `png/cars`
- OK: `gain/carsDPM`
- OK: `gain/carsIRT2`
- OK: `gain/carsIRT4`
- OK: `png/buildings_missing1`
- OK: `png/buildings_missing2`
- OK: `png/buildings_missing3`
- OK: `png/buildings_missing4`

## 样本检查
```json
{
  "map_id": 1,
  "tx_id": 0,
  "files": {
    "buildings": {
      "path": "RadioMapSeer/png/buildings_complete/1.png",
      "shape": [
        256,
        256
      ],
      "dtype": "uint8",
      "min": 0.0,
      "max": 255.0,
      "unique_count": 2
    },
    "antenna": {
      "path": "RadioMapSeer/png/antennas/1_0.png",
      "shape": [
        256,
        256
      ],
      "dtype": "uint8",
      "min": 0.0,
      "max": 255.0,
      "unique_count": 2
    },
    "dpm": {
      "path": "RadioMapSeer/gain/DPM/1_0.png",
      "shape": [
        256,
        256
      ],
      "dtype": "uint8",
      "min": 0.0,
      "max": 255.0,
      "unique_count": 215
    },
    "irt2": {
      "path": "RadioMapSeer/gain/IRT2/1_0.png",
      "shape": [
        256,
        256
      ],
      "dtype": "uint8",
      "min": 0.0,
      "max": 249.0,
      "unique_count": 187
    },
    "irt4": {
      "path": "RadioMapSeer/gain/IRT4/1_0.png",
      "shape": [
        256,
        256
      ],
      "dtype": "uint8",
      "min": 0.0,
      "max": 249.0,
      "unique_count": 220
    }
  }
}
```
