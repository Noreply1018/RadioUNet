# Fixed Receiver Policy 审计

## 结论
- fixed receiver mask 跨 missing setting 不变：`True`。
- target IRT4 hash 跨 missing setting 不变：`True`。
- Tx hash 跨 missing setting 不变：`True`。
- official loader receiver mask 会随 missing building image 变化：`True`。

## Hash 明细
| policy | model | missing | target hash | tx hash | receiver mask hash | receiver points |
| --- | --- | ---: | --- | --- | --- | ---: |
| fixed | C | 0 | `c34d242a797a` | `13aa860402ae` | `723d5c55fe01` | 298 |
| fixed | C | 1 | `c34d242a797a` | `13aa860402ae` | `723d5c55fe01` | 298 |
| fixed | C | 2 | `c34d242a797a` | `13aa860402ae` | `723d5c55fe01` | 298 |
| fixed | C | 4 | `c34d242a797a` | `13aa860402ae` | `723d5c55fe01` | 298 |
| fixed | S | 0 | `b09f37c46cec` | `fd05569f9b62` | `a50c2379b848` | 594 |
| fixed | S | 1 | `b09f37c46cec` | `fd05569f9b62` | `a50c2379b848` | 594 |
| fixed | S | 2 | `b09f37c46cec` | `fd05569f9b62` | `a50c2379b848` | 594 |
| fixed | S | 4 | `b09f37c46cec` | `fd05569f9b62` | `a50c2379b848` | 594 |
| official | C | 0 | `c34d242a797a` | `13aa860402ae` | `d782a1cf64e6` | 299 |
| official | C | 1 | `c34d242a797a` | `13aa860402ae` | `8c56adeed810` | 300 |
| official | C | 2 | `c34d242a797a` | `13aa860402ae` | `4b0c98f66d68` | 299 |
| official | C | 4 | `c34d242a797a` | `13aa860402ae` | `2edb57229b5a` | 300 |
| official | S | 0 | `b09f37c46cec` | `fd05569f9b62` | `7eb2ce512b48` | 595 |
| official | S | 1 | `b09f37c46cec` | `fd05569f9b62` | `320f68d78723` | 595 |
| official | S | 2 | `b09f37c46cec` | `fd05569f9b62` | `82abf28544d5` | 598 |
| official | S | 4 | `b09f37c46cec` | `fd05569f9b62` | `11638b6abf72` | 598 |

最终 gate：`True`。
