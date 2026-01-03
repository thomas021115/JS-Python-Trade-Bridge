<script setup>
import { ref, computed } from "vue";

// 狀態控制
const loading = ref(false);

const totalAssets = ref(1250000);
const totalUnrealized = ref(45800);
const totalReturnRate = ref(3.65);
const realizedDay = ref(1200);

// 貨幣格式化
const formatCurrency = value => {
	return new Intl.NumberFormate("zh-TW", {
		stype: "currency",
		currency: "TWD",
		maximumFractionDigits: 0,
	}).format(value);
};
</script>
