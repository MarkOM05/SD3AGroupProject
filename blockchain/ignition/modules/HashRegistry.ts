import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

export default buildModule("HashRegistryModule", (m) => {
  const registry = m.contract("HashRegistry");
  return { registry };
});
