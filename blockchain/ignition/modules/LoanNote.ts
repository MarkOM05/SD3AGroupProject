import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";
import HashRegistryModule from "./HashRegistry.js";

export default buildModule("LoanNoteModule", (m) => {
  const { registry } = m.useModule(HashRegistryModule);
  const loanNote = m.contract("LoanNote", [m.getAccount(0)]);
  return { loanNote, registry };
});
