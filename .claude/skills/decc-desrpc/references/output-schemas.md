# Output Schemas

详细的 action 返回字段定义。日常使用不需要看，遇到字段不清楚时回查。

## list_channels

```json
{
  "success": true,
  "action": "list_channels",
  "data": {
    "channels": [
      {
        "name": "desrpc.test.http_server",
        "description": "Test HTTP server channel",
        "vgeo_list": ["ROW-TT", "EU"],
        "target_geo_list": ["ROW-TT"],
        "psm_list": ["desrpc.test.http_server"],
        "owners": ["user1"],
        "states": {"ROW-TT": 1}
      }
    ],
    "total": 1,
    "pagination": {"total": 100, "page_number": 1, "page_size": 50}
  }
}
```

## list_data

```json
{
  "success": true,
  "action": "list_data",
  "data": {
    "channel": "desrpc.test.http_server",
    "data_rules": [
      {
        "name": "PUT:/hotsoon/item/path/_like/",
        "channel_name": "desrpc.test.http_server",
        "vgeo_list": ["ROW-TT"],
        "owners": ["user1"],
        "states": {"ROW-TT": 1},
        "direction_pairs": [
          {"source_vgeo": "ROW-TT", "target_vgeo": "EU"}
        ],
        "latest_version_states": {"ROW-TT": {"latestVersion": 3, "latestVersionState": 4}}
      }
    ],
    "total": 5
  }
}
```

`states` 是 channel 维度状态；`latest_version_states.<vgeo>.latestVersionState` 才是版本维度状态。
state 取值：`1=applied`, `2=draft`, `3=reviewing`, `4=cancelled`, `5=rejected`...

## list_data_versions

```json
{
  "success": true,
  "action": "list_data_versions",
  "data": {
    "data_id": "7628400000000000001",
    "versions": [
      {
        "version": 3,
        "states": {"ROW-TT": 4},
        "description": "...",
        "reason": "...",
        "scenario": 9,
        "direction_pairs": [{"source_vgeo": "EU", "target_vgeo": "ROW-TT"}, ...]
      }
    ],
    "total": 3
  }
}
```

## query_caller_channel

```json
{
  "success": true,
  "data": {
    "caller_channels": [
      {
        "caller": "desrpc.test.client",
        "callee": "desrpc.test.http_server",
        "caller_site": "ROW-TT",
        "callee_site": "EU",
        "states": {"ROW-TT": 1},
        "methods": [
          {
            "method": "PUT:/hotsoon/item/path/_like/",
            "level": "method",
            "enabled": true,
            "states": {"ROW-TT": 1}
          }
        ]
      }
    ],
    "total": 1
  }
}
```

## create_channel

```json
{
  "success": true,
  "data": {
    "name": "desrpc.myteam.myservice",
    "channel_id": "7628311760264773900",
    "psm_info": {"psm": "...", "repo": "...", "scm": "...", "region": "i18n"}
  }
}
```

## create_data

```json
{
  "success": true,
  "data": {
    "channel": "desrpc.myteam.myservice",
    "data_name": "Echo",
    "data_id": "7628400000000000001",
    "idl_set": true,
    "url": "https://decc.tiktok-row.net/v3/des-rpc/data?dataId=7628400000000000001&version=1",
    "hint": "You can provide reason and description to enrich the data version via update_data_version action"
  }
}
```

## create_data_version / update_data_version

```json
{
  "success": true,
  "data": {
    "data_id": "7628400000000000001",
    "version": 2,
    "channel_name": "desrpc.myteam.myservice",
    "name": "Echo",
    "updated": true
  }
}
```

## tag_fields

```json
{
  "success": true,
  "data": {
    "data_id": "7632133511629275448",
    "version": 3,
    "default_sync": "YES",
    "applied_catalog": "1.1",
    "applied_entity": "1.2.2",
    "applied_reason": "Required for cross-region item lookup in TT_TTP <> EU mesh",
    "applied_description": "Generic item attribute ...",
    "tagged_fields": 22,
    "skipped_fields": 5,
    "overridden": 8,
    "schema_bytes": 12345
  }
}
```

## submit_data_version (preview, `confirmed=false` / unset)

```json
{
  "success": true,
  "data": {
    "confirmed": false,
    "submitted": false,
    "preview": {
      "data_id": "7632133511629275448",
      "version": 3,
      "scenario": 9,
      "channel": "desrpc.stability.thrift_server",
      "method": "GetItemV3",
      "description": "GetItemV3 cross-region item lookup",
      "reason": "Required for cross-region item lookup in TT_TTP <> EU mesh",
      "explanation": "...",
      "direction_pairs": [
        {"source_vgeo": "EU", "target_vgeo": "US"}, ...
      ],
      "direction_pairs_source": "saved_extra",
      "schema_summary": {
        "leaf_fields_total": 22,
        "with_description": 22,
        "with_texas_catalog": 22,
        "with_tiktok_catalog": 22,
        "with_reason": 22,
        "with_sync_yes": 22,
        "missing_description": [],
        "missing_texas_catalog": [],
        "missing_tiktok_catalog": [],
        "missing_reason": []
      },
      "url": "https://decc.tiktok-row.net/v3/des-rpc/data?dataId=7632133511629275448&version=3"
    },
    "hint": "Submission NOT executed. Show the `preview` block to the user verbatim and obtain explicit approval...",
    "next_command": "gdpa-cli run decc-desrpc --input '{\"action\":\"submit_data_version\",\"data_id\":\"...\",\"version\":3,\"scenario\":9,\"confirmed\":true}'"
  }
}
```

## submit_data_version (confirmed)

```json
{
  "success": true,
  "data": {
    "data_id": "7632133511629275448",
    "version": 3,
    "scenario": 9,
    "confirmed": true,
    "submitted": true,
    "url": "https://decc.tiktok-row.net/v3/des-rpc/data?dataId=7632133511629275448&version=3"
  }
}
```
