# StudioNet deployment evidence

This page records the public deployment and live verification evidence for the
contract-focused ConstitutionGuard release.

## Corrected deployments

- [ConstitutionGuard](https://explorer-studio.genlayer.com/address/0xCD6BdcA9d43fef77D5386877126fED9EBF6f17e4)
- [GovernedExecutorV2](https://explorer-studio.genlayer.com/address/0x63B21c0f8d8C8398651aD057BAf1Ec283d636314)
- [Corrected guard upgrade transaction](https://explorer-studio.genlayer.com/tx/0x2be9795b0dd3630ddfb6e754a10b8b8993941d5d5b424e5d13d2def44f89fee9)

## Live verification

- Constitution registration finalized:
  [0xe1ef9d1a...](https://explorer-studio.genlayer.com/tx/0xe1ef9d1ac5e338c24baf900d382fb0db102b612a2ce3c6ea7dbf67a21c9e81fc)
- Approved proposal evaluation finalized:
  [0xb276b452...](https://explorer-studio.genlayer.com/tx/0xb276b452fb130fa0fd25a33c5b6752b6dec3859b3bb27e5c4bd3f412ba4c6f03)
- Rejected proposal with conflicting evidence:
  [0x68beb464...](https://explorer-studio.genlayer.com/tx/0x68beb464c3483e1a7ef54c5ccb545d56bef46fbb12a0732da0872ee76e223a4d)
- Unavailable source fails closed:
  [0x40356f97...](https://explorer-studio.genlayer.com/tx/0x40356f977b7950c35e85be0ba1b7ecc2832545362ec747bcb9bd7534cf55be04)
- Approved permit invalidated after a constitution update:
  [0x8bb00d55...](https://explorer-studio.genlayer.com/tx/0x8bb00d553ca4f526fcbd30032300b55b371c5524b41efe75741037e8b9a00a64)
- Expired proposal rejected at submission:
  [0x93e1e493...](https://explorer-studio.genlayer.com/tx/0x93e1e493d0ef57269abd9f9b7dbb2719f9eb2bc56b8f41afead79eddde3f83b9)
- Wrong caller rejected:
  [0x657fe38e...](https://explorer-studio.genlayer.com/tx/0x657fe38ee55a4b09e3dc0a78f8aa913699a1b821d8d744b67b6a4d8b573f3b96)
- Executor lifecycle finalized and replay rejected:
  [start](https://explorer-studio.genlayer.com/tx/0x11e4e04ae229fbbbe5bf10a4c4c41c75fa7c44eb454813570a73f12b1146e6f1),
  [finalize](https://explorer-studio.genlayer.com/tx/0x3ad5d74d1617f30a941e45a5c1dcc576c16fa2b28e9609114ffa36a90b666482),
  [replay rejection](https://explorer-studio.genlayer.com/tx/0x775e3221e68d8c0394d2a397cb1b5f4d6309e11b4f532fe32842f3a8308e8c9c)

The full-consensus approval attempt remained undetermined; the successful live
cases above were verified with the StudioNet Leader Only execution mode.

