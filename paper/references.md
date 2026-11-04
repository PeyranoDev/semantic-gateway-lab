# Primary references for the working draft

1. Ignacio Peyrano. *From CRUD to Autonomous Agents: Formal Validation and
   Zero-Trust Security for Semantic Gateways in AI-Native Enterprise Systems.*
   arXiv:2604.25555v1, 2026. https://arxiv.org/abs/2604.25555
2. Ignacio Peyrano. *Semantic Gateway PoC.* Repository, inspected commit
   `1efca4bf0a9e541577ba050e5f4e57ce367bdb68`.
   https://github.com/PeyranoDev/semantic-gateway-poc
3. Guido de Caso, Víctor Braberman, Diego Garbervetsky and Sebastián Uchitel.
   *Validation of Contracts using Enabledness Preserving Finite State Abstractions.*
   ICSE, 2009. Primary research-group bibliography:
   https://lafhis.dc.uba.ar/contractor/contractor.net-web/
4. Guido de Caso, Víctor A. Braberman, Diego Garbervetsky and Sebastián Uchitel.
   *Enabledness-based program abstractions for behavior validation.*
   ACM Transactions on Software Engineering and Methodology, 22(3), Article 25, 2013.
   https://doi.org/10.1145/2491509.2491519
5. Roham Koohestani. *AgentGuard: Runtime Verification of AI Agents.*
   arXiv:2509.23864v1, 2025. https://arxiv.org/abs/2509.23864
6. Nirajan Acharya and Gaurav Kumar Gupta. *A Formal Security Framework for
   MCP-Based AI Agents: Threat Taxonomy, Verification Models, and Defense Mechanisms.*
   arXiv:2604.05969v1, 2026. https://arxiv.org/abs/2604.05969
7. Ting Liu. *From Tool Connection to Execution Control: Benchmarking Security
   Invariants in MCP-Style Agent Runtimes.* arXiv:2606.29073v1, 2026.
   https://arxiv.org/abs/2606.29073
8. Model Context Protocol. *Authorization*, specification 2025-11-25.
   https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization

This is an initial bibliography, not an exhaustive systematic review. Complete
papers and associated artifacts must be read before asserting novelty or comparative
results. No source's reported benchmark numbers are presented as independently
replicated in this repository.

9. Vaggelis Atlidakis, Patrice Godefroid and Marina Polishchuk. *RESTler: Stateful REST API Fuzzing.* ICSE 2019, pp. 748-758. https://doi.org/10.1109/ICSE.2019.00083
   Primary author PDF: https://patricegodefroid.github.io/public_psfiles/icse2019.pdf
10. Van-Thuan Pham, Marcel Böhme and Abhik Roychoudhury. *AFLNET: A Greybox Fuzzer for Network Protocols.* ICST 2020. https://doi.org/10.1109/ICST46399.2020.00062
    Primary author PDF: https://mboehme.github.io/paper/ICST20.AFLNet.pdf

The sequence-mutation follow-up cites these established stateful-generation methods.
RESTler was subsequently executed in the scoped v0.7 pilot; AFLNet remains unexecuted.

11. Vaggelis Atlidakis, Patrice Godefroid and Marina Polishchuk. *Checking Security Properties of Cloud Service REST APIs.* ICST 2020.
    Primary author PDF: https://patricegodefroid.github.io/public_psfiles/icst2020.pdf
12. Davide Corradini, Amedeo Zampieri, Michele Pasqua, Emanuele Viglianisi, Michael Dallago and Mariano Ceccato. *Automated Black-Box Testing of Nominal and Error Scenarios in RESTful APIs.* Software Testing, Verification and Reliability, 2022. https://doi.org/10.1002/stvr.1808
    Author manuscript: https://michelepasqua.github.io/publications/pdfs/STVR22.pdf
    Author publication record: https://profs.scienze.univr.it/~ceccato/papers/2022/stvr2022.html
13. Davide Corradini, Michele Pasqua and Mariano Ceccato. *Automated Black-box Testing of Mass Assignment Vulnerabilities in RESTful APIs.* ICSE 2023.
    Primary abstract/preprint: https://arxiv.org/abs/2301.01261
    Institutional record: https://iris.univr.it/handle/11562/1107429
14. Javier Godoy, Juan Pablo Galeotti, Diego Garbervetsky and Sebastián Uchitel. *Enabledness-based Testing of Object Protocols.* ACM Transactions on Software Engineering and Methodology, 30(2), Article 12, 2021. https://doi.org/10.1145/3415153
    Author-published extended abstract (JAIIO 2022): https://revistas.unlp.edu.ar/JAIIO/article/download/18418/18081/82202
    The complete journal article remains to be reviewed; the inspected primary source is the authors' one-page summary.

The focused source audit, overlap decisions and full-text access limits are documented
in literature-review.md. References [11] and [14] materially change the framing:
security-property checking and enabledness-guided testing have close prior work.
No external tool implementation is included in the measured treatment matrices.

15. Yuanliang Chen, Yu Jiang, Fuchen Ma, Jie Liang, Mingzhe Wang, Chijin Zhou,
    Xun Jiao and Zhuo Su. *EnFuzz: Ensemble Fuzzing with Seed Synchronization
    among Diverse Fuzzers.* USENIX Security 2019, pp. 1967–1983.
    https://www.usenix.org/conference/usenixsecurity19/presentation/chen-yuanliang
    https://www.usenix.org/system/files/sec19-chen-yuanliang.pdf
16. Tai Yue, Pengfei Wang, Yong Tang, Enze Wang, Bo Yu, Kai Lu and Xu Zhou.
    *EcoFuzz: Adaptive Energy-Saving Greybox Fuzzing as a Variant of the Adversarial
    Multi-Armed Bandit.* USENIX Security 2020.
    https://www.usenix.org/system/files/sec20-yue.pdf
17. George T. Klees, Andrew Ruef, Benjamin Cooper, Shiyi Wei and Michael Hicks.
    *Evaluating Fuzz Testing.* ACM CCS 2018. https://doi.org/10.1145/3243734.3243804
    Author bibliography: https://mhicks.me/papers/klees2018fuzzeval.html
    Author preprint: https://arxiv.org/abs/1808.09700

18. Alexander Barabanov, Denis Dergunov, Denis Makrushin and Aleksey Teplov.
    *Automatic detection of access control vulnerabilities via API specification
    processing.* Voprosy kiberbezopasnosti 1(47), pp. 49–65, 2022.
    https://arxiv.org/abs/2201.10833
    https://doi.org/10.21681/2311-3456-2022-1-49-65
    Review scope this round: author metadata and abstract only.

19. Omur Sahin, Man Zhang and Andrea Arcuri. *Enhancing REST API Fuzzing with
    Access Policy Violation Checks and Injection Attacks.* arXiv:2604.00702v1, 2026.
    https://arxiv.org/abs/2604.00702
    Extension of an earlier conference paper whose venue was not verified this round.
    Review scope this round: abstract and the first sections of the HTML full text.
20. Sebastian Burckhardt, Pravesh Kothari, Madanlal Musuvathi and Santosh Nagarakatte.
    *A Randomized Scheduler with Probabilistic Guarantees of Finding Bugs.*
    ASPLOS 2010, pp. 167–178. https://people.cs.rutgers.edu/~sn349/papers/asplos2010.pdf
21. Andrea Arcuri, Muhammad Zohaib Iqbal and Lionel Briand. *Random Testing:
    Theoretical Results and Practical Implications.* IEEE Transactions on Software
    Engineering 38(2), pp. 258–277, 2012. https://doi.org/10.1109/TSE.2011.121
22. Marcel Böhme and Soumya Paul. *A Probabilistic Analysis of the Efficiency of
    Automated Software Testing.* IEEE Transactions on Software Engineering 42(4),
    pp. 345–360, 2016. https://doi.org/10.1109/TSE.2015.2487274
23. Andrea Arcuri and Lionel C. Briand. *A Hitchhiker's Guide to Statistical Tests
    for Assessing Randomized Algorithms in Software Engineering.* Software Testing,
    Verification and Reliability 24(3), pp. 219–250, 2014. https://doi.org/10.1002/stvr.1486
24. Andrea Arcuri. *RESTful API Automated Test Case Generation with EvoMaster.*
    ACM Transactions on Software Engineering and Methodology, 2019.
    Preprint: https://arxiv.org/abs/1901.01538 (volume/issue to verify in ACM DL).
25. Zac Hatfield-Dodds and Dmitry Dygalo. *Deriving Semantics-Aware Fuzzers from
    Web API Schemas.* arXiv:2112.10328, 2021. https://arxiv.org/abs/2112.10328
    Published venue to verify.
26. D. Richard Kuhn, James M. Higdon, James F. Lawrence, Raghu N. Kacker and Yu Lei.
    *Combinatorial Methods for Event Sequence Testing.* ICST 2012 Workshops (CT 2012),
    pp. 601–609. https://doi.org/10.1109/ICST.2012.147

Review scope for 19–26: bibliographic metadata and abstracts verified through
search results; full texts are still to be read before relying on specific claims.
