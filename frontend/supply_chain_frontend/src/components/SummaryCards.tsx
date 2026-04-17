type Props = {
  title: string;
  value: number | string;
};

const SummaryCard: React.FC<Props> = ({ title, value }) => {
  return (
    <div className="bg-white p-4 rounded-2xl shadow-md">
      <h3 className="text-sm text-gray-500">{title}</h3>
      <p className="text-2xl font-bold mt-2">{value}</p>
    </div>
  );
};

export default SummaryCard;